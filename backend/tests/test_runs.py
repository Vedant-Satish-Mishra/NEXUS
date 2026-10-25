"""
Integration tests for Step 1.D.3:
Conversations CRUD, Ownership Isolation (404), and Streaming Runs Endpoint with SSE
"""

import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Base, User, Conversation, Message, Run, RunEvent
from app.api.deps import get_db
from app.main import create_app
from app.core.security import hash_password, create_access_token
from app.api.routes.runs import runs_service
from app.services.runs_service import unregister_active_run
from app.core.llm import LLMProvider


class MockLLMProvider:
    async def chat(self, messages, **opts):
        return "Hello from mock LLM!"

    async def stream(self, messages, **opts):
        for token in ["Hello", " from", " mock", " LLM!"]:
            yield token

    async def structured(self, model, messages, **opts):
        raise NotImplementedError()

    async def aclose(self):
        pass


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def users(test_db):
    async with test_db() as session:
        u1 = User(email="alice@nexus.local", name="Alice", password_hash=hash_password("alicepassword123"))
        u2 = User(email="bob@nexus.local", name="Bob", password_hash=hash_password("bobpassword123"))
        session.add_all([u1, u2])
        await session.commit()
        await session.refresh(u1)
        await session.refresh(u2)

        token_a = create_access_token(u1.id)
        token_b = create_access_token(u2.id)
        return {
            "alice": u1,
            "bob": u2,
            "token_alice": token_a,
            "token_bob": token_b,
        }


@pytest_asyncio.fixture
async def client(test_db, monkeypatch):
    app = create_app()

    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(runs_service, "session_factory", test_db)

    # Monkeypatch default llm provider in app.agents.graph
    from app.agents import graph as agent_graph
    monkeypatch.setattr(agent_graph, "default_llm_provider", MockLLMProvider())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_conversations_crud_and_isolation(client, users):
    """Verify conversations CRUD and strict 404 isolation across users."""
    headers_a = {"Authorization": f"Bearer {users['token_alice']}"}
    headers_b = {"Authorization": f"Bearer {users['token_bob']}"}

    # 1. Alice creates conversation
    create_res = await client.post("/api/v1/conversations", json={"title": "New chat"}, headers=headers_a)
    assert create_res.status_code == 201
    c_data = create_res.json()
    conv_id = c_data["id"]
    assert c_data["title"] == "New chat"

    # 2. Bob cannot GET Alice's conversation -> 404 (not 403)
    bob_get = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers_b)
    assert bob_get.status_code == 404

    # 3. Bob cannot PATCH Alice's conversation -> 404
    bob_patch = await client.patch(f"/api/v1/conversations/{conv_id}", json={"title": "Hacked"}, headers=headers_b)
    assert bob_patch.status_code == 404

    # 4. Bob cannot DELETE Alice's conversation -> 404
    bob_del = await client.delete(f"/api/v1/conversations/{conv_id}", headers=headers_b)
    assert bob_del.status_code == 404

    # 5. Alice renames conversation
    alice_patch = await client.patch(f"/api/v1/conversations/{conv_id}", json={"title": "My Study Plan"}, headers=headers_a)
    assert alice_patch.status_code == 200
    assert alice_patch.json()["title"] == "My Study Plan"

    # 6. Alice lists conversations
    list_res = await client.get("/api/v1/conversations", headers=headers_a)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == conv_id

    # 7. Bob lists conversations -> empty
    bob_list = await client.get("/api/v1/conversations", headers=headers_b)
    assert bob_list.status_code == 200
    assert len(bob_list.json()) == 0


@pytest.mark.asyncio
async def test_run_creation_auto_title_and_message_order(client, users, test_db):
    """
    Verify:
    - User message is saved BEFORE generation
    - Auto-title updates 'New chat' to first message preview
    - Active run creates a run row
    """
    headers_a = {"Authorization": f"Bearer {users['token_alice']}"}

    # Create new conversation with default title
    c_res = await client.post("/api/v1/conversations", json={"title": "New chat"}, headers=headers_a)
    conv_id = c_res.json()["id"]

    # Start run
    prompt = "Explain Dijkstra's algorithm and dynamic programming in detail."
    run_res = await client.post(
        "/api/v1/runs",
        json={"conversation_id": conv_id, "message": prompt},
        headers=headers_a,
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["run_id"]

    # Verify auto-title and user message presence before/after run
    async with test_db() as session:
        c = (await session.execute(select(Conversation).where(Conversation.id == conv_id))).scalar_one()
        assert c.title.startswith("Explain Dijkstra's algorithm")

        msgs = (await session.execute(select(Message).where(Message.conversation_id == conv_id))).scalars().all()
        assert len(msgs) == 1
        assert msgs[0].role == "user"
        assert msgs[0].content == prompt

    # Clean up active run for next test
    await unregister_active_run(users["alice"].id, run_id)


@pytest.mark.asyncio
async def test_run_streaming_sse_events(client, users, test_db):
    """
    Verify SSE stream delivers:
    run_started -> node_started -> token* -> node_finished -> final
    and persists assistant message on final.
    """
    headers_a = {"Authorization": f"Bearer {users['token_alice']}"}

    c_res = await client.post("/api/v1/conversations", json={"title": "Algorithms"}, headers=headers_a)
    conv_id = c_res.json()["id"]

    prompt = "What is Big-O notation?"
    run_res = await client.post(
        "/api/v1/runs",
        json={"conversation_id": conv_id, "message": prompt},
        headers=headers_a,
    )
    run_id = run_res.json()["run_id"]

    # Stream SSE events
    sse_res = await client.get(f"/api/v1/runs/{run_id}/events", headers=headers_a)
    assert sse_res.status_code == 200
    assert "text/event-stream" in sse_res.headers["content-type"]

    lines = sse_res.text.strip().split("\n\n")
    event_types = []
    received_tokens = []

    for block in lines:
        if not block:
            continue
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_types.append(line.replace("event: ", "").strip())
            elif line.startswith("data: "):
                payload = json.loads(line.replace("data: ", ""))
                if payload.get("type") == "token":
                    received_tokens.append(payload.get("content"))

    # Assert event pipeline
    assert "run_started" in event_types
    assert "node_started" in event_types
    assert "token" in event_types
    assert "node_finished" in event_types
    assert "final" in event_types
    assert "".join(received_tokens) == "Hello from mock LLM!"

    # Assert assistant message was saved to database
    async with test_db() as session:
        msgs = (
            await session.execute(
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.created_at)
            )
        ).scalars().all()
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"
        assert msgs[1].content == "Hello from mock LLM!"

        # Assert run is marked completed
        r = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()
        assert r.status == "completed"
        assert r.latency_ms is not None


@pytest.mark.asyncio
async def test_concurrency_one_active_run_per_user(client, users):
    """Verify that a second run creation while one is already active is rejected with 409."""
    headers_a = {"Authorization": f"Bearer {users['token_alice']}"}

    c_res = await client.post("/api/v1/conversations", json={"title": "Chat"}, headers=headers_a)
    conv_id = c_res.json()["id"]

    # Launch first run
    r1 = await client.post(
        "/api/v1/runs",
        json={"conversation_id": conv_id, "message": "First message"},
        headers=headers_a,
    )
    assert r1.status_code == 201
    run_1_id = r1.json()["run_id"]

    # Attempt to launch second run concurrently for same user
    r2 = await client.post(
        "/api/v1/runs",
        json={"conversation_id": conv_id, "message": "Second concurrent message"},
        headers=headers_a,
    )
    assert r2.status_code == 409
    assert "Another run is currently active" in r2.json()["detail"]

    # Clean up
    await unregister_active_run(users["alice"].id, run_1_id)

