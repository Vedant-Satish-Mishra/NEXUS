"""
Unit and Integration Tests for Step 1.C.1:
Embedder & VectorStore with Strict Isolation by Construction
"""

import math
import shutil
import tempfile
import pytest
import pytest_asyncio

from app.schemas.core import Principal
from app.rag.embeddings import FastEmbedEmbedder, BGE_QUERY_PREFIX
from app.rag.vectorstore import VectorStore, scope_filter


@pytest.fixture
def temp_chroma_dir():
    d = tempfile.mkdtemp(prefix="nexus_chroma_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.asyncio
async def test_embedder_query_prefix():
    """Verify BGE query prefix is properly applied to embed_query."""
    embedder = FastEmbedEmbedder()
    # Mocking internal embed sync to test prefix application
    orig_embed = embedder._embed_query_sync
    captured = []

    def mock_embed(text: str):
        captured.append(text)
        return [0.0] * 384

    embedder._embed_query_sync = mock_embed
    await embedder.embed_query("What is quicksort?")
    assert len(captured) == 1
    assert captured[0].startswith(BGE_QUERY_PREFIX)
    assert "What is quicksort?" in captured[0]


@pytest.mark.asyncio
async def test_embedder_semantic_sanity_pair():
    """Verify that a relevant sentence pair yields higher cosine similarity than an unrelated pair."""
    embedder = FastEmbedEmbedder()
    query = "How does binary search work on sorted arrays?"
    doc_relevant = "Binary search divides the sorted array in half repeatedly with O(log n) time complexity."
    doc_unrelated = "French cuisine features baguettes, cheese, wine and croissants."

    q_vec = await embedder.embed_query(query)
    docs_vecs = await embedder.embed_documents([doc_relevant, doc_unrelated])

    def cosine_sim(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        return dot / (norm_a * norm_b)

    sim_rel = cosine_sim(q_vec, docs_vecs[0])
    sim_unrel = cosine_sim(q_vec, docs_vecs[1])

    assert sim_rel > sim_unrel, f"Relevant ({sim_rel}) should score higher than unrelated ({sim_unrel})"


def test_scope_filter_construction():
    """Verify scope_filter builds correct ChromaDB logical clauses."""
    # With conversation_id and system
    p1 = Principal(user_id="user_123", conversation_id="conv_abc")
    f1 = scope_filter(p1, include_system=True)
    assert "$or" in f1
    assert len(f1["$or"]) == 3

    # Without conversation_id and no system
    p2 = Principal(user_id="user_456", conversation_id=None)
    f2 = scope_filter(p2, include_system=False)
    assert f2 == {"$and": [{"user_id": "user_456"}, {"scope": "personal"}]}


def test_two_user_and_two_conversation_isolation(temp_chroma_dir):
    """
    Two-user test:
    - User A's personal chunks NEVER appear in User B's results
    - A chat-scoped chunk from Conversation 1 NEVER appears in Conversation 2
    """
    store = VectorStore(path=temp_chroma_dir)

    user_a = Principal(user_id="alice", conversation_id="conv_1")
    user_a_c2 = Principal(user_id="alice", conversation_id="conv_2")
    user_b = Principal(user_id="bob", conversation_id="conv_3")

    dummy_emb = [0.1] * 384

    # Alice uploads:
    # 1. Personal chunk
    store.upsert_user_chunks(
        principal=user_a,
        file_id="f_a_personal",
        scope="personal",
        ids=["chunk_a_p1"],
        documents=["Alice personal secret notes on Python."],
        embeddings=[dummy_emb],
        metadatas=[{"chunk_index": 0}],
    )
    # 2. Chat 1 chunk
    store.upsert_user_chunks(
        principal=user_a,
        file_id="f_a_c1",
        scope="chat",
        ids=["chunk_a_c1"],
        documents=["Alice conversation 1 specific context."],
        embeddings=[dummy_emb],
        metadatas=[{"chunk_index": 0}],
    )

    # Bob uploads:
    # 1. Personal chunk
    store.upsert_user_chunks(
        principal=user_b,
        file_id="f_b_personal",
        scope="personal",
        ids=["chunk_b_p1"],
        documents=["Bob personal notes on database indices."],
        embeddings=[dummy_emb],
        metadatas=[{"chunk_index": 0}],
    )

    # 1. Bob queries -> MUST ONLY see Bob's chunks, never Alice's
    bob_results = store.query_user_kb(user_b, dummy_emb, n_results=10, include_system=False)
    bob_ids = [r["id"] for r in bob_results]
    assert "chunk_b_p1" in bob_ids
    assert "chunk_a_p1" not in bob_ids
    assert "chunk_a_c1" not in bob_ids

    # 2. Alice in Conversation 1 queries -> MUST see personal + conv_1, but NOT Bob
    alice_c1_results = store.query_user_kb(user_a, dummy_emb, n_results=10, include_system=False)
    alice_c1_ids = [r["id"] for r in alice_c1_results]
    assert "chunk_a_p1" in alice_c1_ids
    assert "chunk_a_c1" in alice_c1_ids
    assert "chunk_b_p1" not in alice_c1_ids

    # 3. Alice in Conversation 2 queries -> MUST see personal, but NOT conv_1 and NOT Bob
    alice_c2_results = store.query_user_kb(user_a_c2, dummy_emb, n_results=10, include_system=False)
    alice_c2_ids = [r["id"] for r in alice_c2_results]
    assert "chunk_a_p1" in alice_c2_ids
    assert "chunk_a_c1" not in alice_c2_ids
    assert "chunk_b_p1" not in alice_c2_ids


def test_delete_cascade(temp_chroma_dir):
    """Verify delete_file deletes all vectors for that file owned by principal."""
    store = VectorStore(path=temp_chroma_dir)
    user_a = Principal(user_id="alice", conversation_id="conv_1")
    user_b = Principal(user_id="bob", conversation_id="conv_2")
    emb = [0.2] * 384

    # Alice uploads 2 chunks for file_1 and 1 chunk for file_2
    store.upsert_user_chunks(
        principal=user_a,
        file_id="file_1",
        scope="personal",
        ids=["f1_c1", "f1_c2"],
        documents=["File 1 Chunk 1", "File 1 Chunk 2"],
        embeddings=[emb, emb],
        metadatas=[{"chunk_index": 0}, {"chunk_index": 1}],
    )
    store.upsert_user_chunks(
        principal=user_a,
        file_id="file_2",
        scope="personal",
        ids=["f2_c1"],
        documents=["File 2 Chunk 1"],
        embeddings=[emb],
        metadatas=[{"chunk_index": 0}],
    )

    # Bob attempts to delete Alice's file_1 -> Should delete 0 chunks!
    deleted_by_bob = store.delete_file(user_b, "file_1")
    assert deleted_by_bob == 0

    # Alice's file_1 chunks must still exist
    alice_res = store.query_user_kb(user_a, emb, n_results=5, include_system=False)
    alice_ids = [r["id"] for r in alice_res]
    assert "f1_c1" in alice_ids
    assert "f1_c2" in alice_ids

    # Alice deletes her own file_1 -> Should delete 2 chunks
    deleted_by_alice = store.delete_file(user_a, "file_1")
    assert deleted_by_alice == 2

    # Query again: file_1 chunks are gone, file_2 chunk remains
    alice_res_after = store.query_user_kb(user_a, emb, n_results=5, include_system=False)
    alice_ids_after = [r["id"] for r in alice_res_after]
    assert "f1_c1" not in alice_ids_after
    assert "f1_c2" not in alice_ids_after
    assert "f2_c1" in alice_ids_after


def test_persistence_across_reconnect(temp_chroma_dir):
    """Verify vectors persist across PersistentClient restarts."""
    # Write with store 1
    store1 = VectorStore(path=temp_chroma_dir)
    user = Principal(user_id="charlie", conversation_id=None)
    emb = [0.3] * 384

    store1.upsert_user_chunks(
        principal=user,
        file_id="persist_file",
        scope="personal",
        ids=["p_chunk_1"],
        documents=["Persistent content across reloads."],
        embeddings=[emb],
        metadatas=[{"chunk_index": 0}],
    )

    # Re-instantiate VectorStore on the same directory
    store2 = VectorStore(path=temp_chroma_dir)
    res = store2.query_user_kb(user, emb, n_results=5, include_system=False)
    assert len(res) == 1
    assert res[0]["id"] == "p_chunk_1"
    assert res[0]["text"] == "Persistent content across reloads."


def test_memory_crud_and_isolation(temp_chroma_dir):
    """Verify memory storage, retrieval, and user isolation."""
    store = VectorStore(path=temp_chroma_dir)
    u1 = Principal(user_id="user_1")
    u2 = Principal(user_id="user_2")
    emb = [0.15] * 384

    store.upsert_memory(u1, "mem_1", "long_term", "User prefers TypeScript over JavaScript", emb)
    store.upsert_memory(u2, "mem_2", "long_term", "User prefers Python", emb)

    # User 1 query
    u1_mems = store.query_memory(u1, emb)
    assert len(u1_mems) == 1
    assert u1_mems[0]["id"] == "mem_1"

    # User 2 query
    u2_mems = store.query_memory(u2, emb)
    assert len(u2_mems) == 1
    assert u2_mems[0]["id"] == "mem_2"

    # Delete single memory
    store.delete_memory(u1, "mem_1")
    assert len(store.query_memory(u1, emb)) == 0
    assert len(store.query_memory(u2, emb)) == 1
