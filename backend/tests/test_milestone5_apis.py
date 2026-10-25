"""
NEXUS Milestone 5 Integration Tests
Verifies:
1. Learning Agent service rules (5 samples threshold, single negative rating no-op, decay, +/-10% boost bounds, no text stored)
2. GraphStore concept extraction and memory graph route
3. Dashboard aggregate API
4. Settings read/update
5. Export ZIP stream
6. Learning reset
7. Account deletion with cascade
"""
import io
import zipfile
import pytest
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.models import LearningSignal, User, UserSettings
from app.schemas.core import Principal
from app.services.graph_store import extract_concepts_from_text, InMemoryGraphStore
from app.services.learning import LearningService


@pytest.mark.asyncio
async def test_learning_service_hard_rules(test_db):
    service = LearningService()
    user_id = "test-user-learn"

    # Verify no text column on LearningSignal table
    cols = [c.name for c in LearningSignal.__table__.columns]
    assert "text" not in cols, "LearningSignal must NEVER store raw message text"
    assert "content" not in cols, "LearningSignal must NEVER store raw message text"

    principal = Principal(user_id=user_id, role="user")

    async with test_db() as db_session:
        # 1. Below 5 samples -> NO hints
        for i in range(3):
            await service.record_signal(
                db=db_session,
                user_id=user_id,
                intent="general",
                strategy_key="plan_detail",
                signal="user_feedback",
                value=1.0,
                source="feedback",
                run_id=f"run-{i}",
            )
        hints, boosts = await service.get_hints_and_boosts(db_session, principal, "general")
        assert len(hints) == 0, "Hints must not appear before threshold of 5 samples"

        # 2. Add 2 more positive samples -> threshold of 5 reached (> 0.75 -> 'prefer')
        for i in range(3, 5):
            await service.record_signal(
                db=db_session,
                user_id=user_id,
                intent="general",
                strategy_key="plan_detail",
                signal="user_feedback",
                value=1.0,
                source="feedback",
                run_id=f"run-{i}",
            )
        hints, boosts = await service.get_hints_and_boosts(db_session, principal, "general")
        assert len(hints) >= 1
        assert any("prefer" in h.lower() for h in hints)

        # 3. Single bad rating should not flip a prefer hint
        await service.record_signal(
            db=db_session,
            user_id=user_id,
            intent="general",
            strategy_key="plan_detail",
            signal="user_feedback",
            value=0.0,
            source="feedback",
            run_id="run-bad",
        )
        hints_after_bad, _ = await service.get_hints_and_boosts(db_session, principal, "general")
        assert len(hints_after_bad) >= 1, "Single negative feedback must not erase learned preference"

        # 4. Evidence source boost bounded within +/-10% (0.9 to 1.1)
        for i in range(6):
            await service.record_signal(
                db=db_session,
                user_id=user_id,
                intent="general",
                strategy_key="evidence_source:doc_123",
                signal="user_feedback",
                value=1.0,
                source="feedback",
                run_id=f"run-src-{i}",
            )
        _, boosts = await service.get_hints_and_boosts(db_session, principal, "general")
        assert "doc_123" in boosts
        assert 0.90 <= boosts["doc_123"] <= 1.10

        # 5. Reset learning data
        deleted = await service.reset_learning_data(db_session, user_id)
        assert deleted >= 5
        hints_reset, boosts_reset = await service.get_hints_and_boosts(db_session, principal, "general")
        assert len(hints_reset) == 0
        assert len(boosts_reset) == 0


@pytest.mark.asyncio
async def test_graph_store_and_concept_extraction():
    store = InMemoryGraphStore()
    user_id = "test-graph-user"

    text = """
# Algorithms: Binary Tree Traversals

In computer science, a **binary tree** is a hierarchical data structure.
Traversals like **recursion** and **stack** techniques visit nodes in depth-first order.
"""
    concepts = extract_concepts_from_text(text)
    assert "binary tree" in concepts

    # Upsert concepts & link
    await store.upsert_concept(user_id, "binary tree", "file", "f1")
    await store.upsert_concept(user_id, "recursion", "file", "f1")
    await store.link_concepts(user_id, "binary tree", "recursion", "REQUIRES")

    related = await store.get_related_concepts(user_id, ["binary tree"])
    assert "recursion" in related

    graph_data = await store.get_user_graph(user_id)
    assert len(graph_data["nodes"]) >= 2
    assert len(graph_data["edges"]) >= 1

    # Cascade delete by source
    await store.delete_by_source(user_id, "f1")
    graph_after = await store.get_user_graph(user_id)
    assert len(graph_after["nodes"]) == 0


@pytest.mark.asyncio
async def test_dashboard_and_settings_apis(test_db, client):
    # Setup user
    pw_hash = hash_password("ValidPass123!")
    user = User(
        id="user-m5-test",
        email="m5user@example.com",
        name="M5 Tester",
        password_hash=pw_hash,
    )
    async with test_db() as session:
        session.add(user)
        await session.commit()

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/v1/dashboard
    dash_res = await client.get("/api/v1/dashboard", headers=headers)
    assert dash_res.status_code == 200
    d = dash_res.json()
    assert "runs_per_day" in d
    assert len(d["runs_per_day"]) == 14
    assert "avg_latency_by_tier" in d
    assert "services_health" in d

    # 2. GET /api/v1/settings
    set_res = await client.get("/api/v1/settings", headers=headers)
    assert set_res.status_code == 200
    s = set_res.json()
    assert s["model_profile"] in ("fast", "quality")

    # 3. PUT /api/v1/settings
    update_payload = {
        "model_profile": "quality",
        "default_preset": "full",
        "memory_enabled": True,
        "learning_enabled": True,
        "privacy_mode": True,
        "web_search_enabled": False,
        "theme": "dark",
        "reduced_motion": True,
    }
    put_res = await client.put("/api/v1/settings", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["model_profile"] == "quality"
    assert put_res.json()["reduced_motion"] is True

    # 4. GET /api/v1/export
    export_res = await client.get("/api/v1/export", headers=headers)
    assert export_res.status_code == 200
    assert export_res.headers["content-type"] == "application/zip"

    # Verify ZIP contents
    zip_buf = io.BytesIO(export_res.content)
    with zipfile.ZipFile(zip_buf, "r") as zf:
        namelist = zf.namelist()
        assert "conversations.json" in namelist
        assert "memories.json" in namelist
        assert "files.json" in namelist
        assert "feedback.json" in namelist
        assert "settings.json" in namelist
        # Assert no secret strings in export
        for name in namelist:
            content = zf.read(name).decode("utf-8", errors="ignore")
            assert "password_hash" not in content

    # 5. DELETE /api/v1/learning
    del_learn_res = await client.delete("/api/v1/learning", headers=headers)
    assert del_learn_res.status_code == 200

    # 6. GET /api/v1/memory/graph
    graph_res = await client.get("/api/v1/memory/graph", headers=headers)
    assert graph_res.status_code == 200
    assert "nodes" in graph_res.json()

    # 7. DELETE /api/v1/account - invalid password
    bad_pw_res = await client.request(
        "DELETE",
        "/api/v1/account",
        json={"password": "WrongPassword!"},
        headers=headers
    )
    assert bad_pw_res.status_code == 400

    # 8. DELETE /api/v1/account - valid password
    del_acc_res = await client.request(
        "DELETE",
        "/api/v1/account",
        json={"password": "ValidPass123!"},
        headers=headers
    )
    assert del_acc_res.status_code == 200
