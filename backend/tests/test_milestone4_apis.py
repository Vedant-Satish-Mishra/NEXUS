"""
Integration Tests for Milestone 4 APIs (Tools, Feedback, Rate Limits, Workflows)
"""
import pytest
from httpx import AsyncClient
from app.core.rate_limit import check_rate_limit, reset_rate_limits
from app.core.security import create_access_token, hash_password
from app.db.models import Conversation, Message, Run, User
from fastapi import HTTPException


async def create_user_and_token(session_factory, username="m4_user", email="m4@nexus.local"):
    async with session_factory() as db:
        user = User(
            id=f"uid_{username}",
            email=email,
            name=username,
            password_hash=hash_password("NexusPass123!"),
        )
        db.add(user)
        await db.commit()
    token = create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_tools_list_endpoint(client: AsyncClient, test_db):
    user, token = await create_user_and_token(test_db, "user_tools", "tools@nexus.local")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/tools", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4

    names = {t["name"]: t for t in data}
    assert "calculator" in names
    assert names["calculator"]["permission"] == "auto"

    assert "python" in names
    assert names["python"]["permission"] == "needs_approval"

    assert "web_search" in names
    assert names["web_search"]["permission"] == "disabled"


@pytest.mark.asyncio
async def test_feedback_flow(client: AsyncClient, test_db):
    user, token = await create_user_and_token(test_db, "user_fb", "fb@nexus.local")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a conversation and assistant message for user
    conv_id = "conv_fb_test"
    msg_id = "msg_asst_fb"

    async with test_db() as db:
        conv = Conversation(id=conv_id, user_id=user.id, title="Feedback Test")
        db.add(conv)
        msg = Message(id=msg_id, conversation_id=conv_id, role="assistant", content="Here is an answer.")
        db.add(msg)
        await db.commit()

    # 2. Submit positive feedback (+1)
    fb_payload = {
        "message_id": msg_id,
        "rating": 1,
        "comment": "Super helpful explanation!",
    }
    resp = await client.post("/api/v1/feedback", json=fb_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["rating"] == 1

    # 3. Retrieve feedback
    get_resp = await client.get(f"/api/v1/feedback/{msg_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["rating"] == 1
    assert get_resp.json()["comment"] == "Super helpful explanation!"

    # 4. Toggle feedback off (rating: 0)
    toggle_payload = {"message_id": msg_id, "rating": 0}
    resp_off = await client.post("/api/v1/feedback", json=toggle_payload, headers=headers)
    assert resp_off.status_code == 200
    assert resp_off.json()["status"] == "removed"

    # 5. Retrieve again: should be 0
    get_resp_after = await client.get(f"/api/v1/feedback/{msg_id}", headers=headers)
    assert get_resp_after.json()["rating"] == 0


@pytest.mark.asyncio
async def test_feedback_isolation(client: AsyncClient, test_db):
    user, token = await create_user_and_token(test_db, "user_fb_iso", "fb_iso@nexus.local")
    headers = {"Authorization": f"Bearer {token}"}
    # Feedback on non-existent or other user's message returns 404
    fb_payload = {"message_id": "other_users_message_id", "rating": 1}
    resp = await client.post("/api/v1/feedback", json=fb_payload, headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rate_limiter_exceeded():
    reset_rate_limits()
    uid = "rate_test_user"

    # Limit 3 per 60 seconds
    check_rate_limit(uid, "test_action", limit=3, window_seconds=60)
    check_rate_limit(uid, "test_action", limit=3, window_seconds=60)
    check_rate_limit(uid, "test_action", limit=3, window_seconds=60)

    # 4th call raises 429
    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(uid, "test_action", limit=3, window_seconds=60)
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    reset_rate_limits()


@pytest.mark.asyncio
async def test_list_runs_pagination_and_filter(client: AsyncClient, test_db):
    user, token = await create_user_and_token(test_db, "user_wf", "wf@nexus.local")
    headers = {"Authorization": f"Bearer {token}"}

    # Insert a couple of runs
    async with test_db() as db:
        conv = Conversation(id="conv_runs_wf", user_id=user.id, title="Workflow Run Test")
        db.add(conv)
        r1 = Run(id="run_wf_1", conversation_id="conv_runs_wf", user_id=user.id, status="completed", tier=1)
        r2 = Run(id="run_wf_2", conversation_id="conv_runs_wf", user_id=user.id, status="failed", tier=2)
        db.add_all([r1, r2])
        await db.commit()

    # Query all
    resp = await client.get("/api/v1/runs?limit=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert "items" in data

    # Query filtered by status
    resp_filtered = await client.get("/api/v1/runs?status=failed", headers=headers)
    assert resp_filtered.status_code == 200
    assert all(item["status"] == "failed" for item in resp_filtered.json()["items"])
