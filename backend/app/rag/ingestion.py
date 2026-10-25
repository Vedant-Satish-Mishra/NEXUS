"""
NEXUS Document Ingestion Engine
Step 2.C.1 — Idempotent chunk embedding, deterministic hashing, and VectorStore ingestion
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from app.rag.chunking import DocumentChunk, chunk_document
from app.rag.embeddings import get_embedder
from app.rag.loaders import load_file
from app.rag.vectorstore import VectorStore
from app.schemas.core import Principal

logger = logging.getLogger("nexus.rag.ingestion")


def compute_chunk_id(file_id: str, chunk_index: int, text: str) -> str:
    """Deterministic chunk ID: sha1(file_id | chunk_index | text)."""
    raw = f"{file_id}|{chunk_index}|{text}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


async def ingest_chunks(
    chunks: List[DocumentChunk],
    file_id: str,
    scope: str = "system",
    principal: Optional[Principal] = None,
    vectorstore: Optional[VectorStore] = None,
    batch_size: int = 32
) -> int:
    """
    Embeds chunks in batches of 32 and upserts into VectorStore.
    If scope == 'system', upserts to kb_system.
    If scope in ('personal', 'chat'), upserts to kb_user with principal isolation.
    """
    if not chunks:
        return 0

    vs = vectorstore or VectorStore()
    embedder = get_embedder()

    total_ingested = 0

    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]
        ids = [compute_chunk_id(file_id, c.chunk_index, c.text) for c in batch]
        
        # Embed batch
        embeddings = await embedder.embed_documents(texts)

        metadatas: List[Dict[str, Any]] = [
            {
                "file_id": file_id,
                "source": c.source,
                "topic": c.topic,
                "heading_path": c.heading_path,
                "chunk_index": c.chunk_index,
                "page": c.page or 1
            }
            for c in batch
        ]

        if scope == "system":
            vs.upsert_system_chunks(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            if not principal:
                raise ValueError("Principal is required for user-scoped ingestion")
            vs.upsert_user_chunks(
                principal=principal,
                file_id=file_id,
                scope=scope,
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )

        total_ingested += len(batch)

    logger.info(f"Ingested {total_ingested} chunks for file_id='{file_id}' (scope='{scope}')")
    return total_ingested


async def ingest_file_path(
    path_str: str,
    file_id: str,
    scope: str = "system",
    principal: Optional[Principal] = None,
    vectorstore: Optional[VectorStore] = None
) -> int:
    """Loads, chunks, and ingests a single file."""
    doc = load_file(path_str)
    if not doc:
        logger.warning(f"Could not load file at {path_str}")
        return 0

    chunks = chunk_document(doc)
    return await ingest_chunks(
        chunks=chunks,
        file_id=file_id,
        scope=scope,
        principal=principal,
        vectorstore=vectorstore
    )
