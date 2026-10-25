"""
NEXUS Authorization & Multi-Tenant Isolation Test Matrix (Step 3.D.2)
Verifies that User A accessing any resource belonging to User B returns 404 Not Found.
Tests cover:
- Conversations CRUD isolation
- Runs & Events isolation
- Files & Ingestion isolation
- Memories & Proposals isolation
- VectorStore Principal filter isolation
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import create_access_token
from app.db.models import Conversation, FileRecord, Memory, MemoryProposalRecord, Run, User
from app.main import create_app
from app.schemas.core import Principal
from app.rag.vectorstore import VectorStore


@pytest_asyncio.fixture
async def authz_setup(test_db):
    """Sets up User Alice and User Bob with owned resources across all tables."""
    async with test_db() as session:
        # Create Alice
        alice = User(
            email="alice.authz@nexus.local",
            name="Alice Authz",
            password_hash="fakehash",
        )
        # Create Bob
        bob = User(
            email="bob.authz@nexus.local",
            name="Bob Authz",
            password_hash="fakehash",
        )
        session.add_all([alice, bob])
        await session.flush()

        # Alice's conversation & run
        conv_alice = Conversation(user_id=alice.id, title="Alice Secret")
        session.add(conv_alice)
        await session.flush()

        run_alice = Run(conversation_id=conv_alice.id, user_id=alice.id, status="completed", tier=1)
        session.add(run_alice)
        await session.flush()

        # Alice's file
        file_alice = FileRecord(
            user_id=alice.id,
            conversation_id=conv_alice.id,
            scope="chat",
            filename="alice_plans.pdf",
            mime="application/pdf",
            size=1024,
            sha256="alice_sha256_mock_hash",
            status="ready",
        )
        session.add(file_alice)
        await session.flush()

        # Alice's memory & proposal
        mem_alice = Memory(
            user_id=alice.id,
            kind="long_term",
            content="Alice prefers Python over Java",
            active=True
        )
        prop_alice = MemoryProposalRecord(
            user_id=alice.id,
            run_id=run_alice.id,
            kind="long_term",
            content="Alice's candidate memory",
            status="pending"
        )
        session.add_all([mem_alice, prop_alice])
        await session.commit()

        token_alice = create_access_token(alice.id)
        token_bob = create_access_token(bob.id)

        return {
            "token_alice": token_alice,
            "token_bob": token_bob,
            "alice_ids": {
                "conversation": conv_alice.id,
                "run": run_alice.id,
                "file": file_alice.id,
                "memory": mem_alice.id,
                "proposal": prop_alice.id,
            }
        }


# Resource routes matrix: (HTTP method, URL template, body)
AUTHZ_ROUTES_MATRIX = [
    ("GET", "/api/v1/conversations/{conversation}", None),
    ("PATCH", "/api/v1/conversations/{conversation}", {"title": "Hacked"}),
    ("DELETE", "/api/v1/conversations/{conversation}", None),
    ("GET", "/api/v1/conversations/{conversation}/agents", None),
    ("PUT", "/api/v1/conversations/{conversation}/agents", {
        "preset": "fast", "enabled_agents": ["controller", "reasoning"], "auto_approve_plans": False, "model_profile": "fast"
    }),
    ("GET", "/api/v1/runs/{run}", None),
    ("GET", "/api/v1/files/{file}", None),
    ("DELETE", "/api/v1/files/{file}", None),
    ("POST", "/api/v1/files/{file}/promote", None),
    ("PATCH", "/api/v1/memory/{memory}", {"content": "Hacked memory"}),
    ("DELETE", "/api/v1/memory/{memory}", None),
    ("POST", "/api/v1/memory/proposals/{proposal}/decision", {"action": "accept"}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path_template,payload", AUTHZ_ROUTES_MATRIX)
async def test_authz_isolation_matrix(client, authz_setup, method, path_template, payload):
    """
    Asserts that Bob making requests with Alice's resource IDs gets strictly 404 Not Found.
    Never 403 or 200 (which leaks existence).
    """
    token_bob = authz_setup["token_bob"]
    alice_ids = authz_setup["alice_ids"]

    # Format URL with Alice's ID
    url = path_template.format(**alice_ids)
    headers = {"Authorization": f"Bearer {token_bob}"}

    if method == "GET":
        resp = await client.get(url, headers=headers)
    elif method == "POST":
        resp = await client.post(url, json=payload, headers=headers)
    elif method == "PATCH":
        resp = await client.patch(url, json=payload, headers=headers)
    elif method == "DELETE":
        resp = await client.delete(url, headers=headers)
    elif method == "PUT":
        resp = await client.put(url, json=payload, headers=headers)
    else:
        pytest.fail(f"Unsupported method: {method}")

    assert resp.status_code == 404, f"Expected 404 for Bob calling {method} {url}, got {resp.status_code} ({resp.text})"


@pytest.mark.asyncio
async def test_vectorstore_principal_isolation():
    """Verify VectorStore strictly prevents cross-user vector discovery."""
    vs = VectorStore()
    p_alice = Principal(user_id="usr_alice_isolated", conversation_id="conv_1")
    p_bob = Principal(user_id="usr_bob_isolated", conversation_id="conv_2")

    # Upsert Alice's private chunk
    vs.upsert_user_chunks(
        principal=p_alice,
        file_id="f_alice",
        scope="personal",
        ids=["chunk_alice_private_1"],
        documents=["Alice financial statement balance 1000000 dollars"],
        embeddings=[[0.05] * 384],
        metadatas=[{"topic": "Finance"}]
    )

    # Bob searches with the exact same embedding
    bob_results = vs.query_user_and_system(
        principal=p_bob,
        query_embedding=[0.05] * 384,
        n_results=10,
        include_system=False
    )

    # Bob must NEVER find Alice's chunk
    found_ids = [r["id"] for r in bob_results]
    assert "chunk_alice_private_1" not in found_ids
