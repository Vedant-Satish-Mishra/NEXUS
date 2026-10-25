"""
Unit Tests: Backend Foundation & Health Endpoint (Step 1.D.1)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.db.models import User, Conversation, Message, Run, Base
from app.core.config import settings


@pytest.mark.asyncio
async def test_health_endpoint_contract():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "database" in data["services"]
        assert "chroma" in data["services"]
        assert "ollama" in data["services"]


def test_models_metadata():
    # Assert all tables exist in metadata
    table_names = Base.metadata.tables.keys()
    assert "users" in table_names
    assert "conversations" in table_names
    assert "chat_agent_configs" in table_names
    assert "messages" in table_names
    assert "runs" in table_names
    assert "run_events" in table_names
    assert "files" in table_names
    assert "memory_proposals" in table_names
    assert "memories" in table_names
    assert "tool_executions" in table_names
    assert "feedback" in table_names
    assert "learning_signals" in table_names
    assert "user_settings" in table_names


def test_config_jwt_and_env():
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_MINUTES > 0
    assert settings.REFRESH_TOKEN_DAYS > 0
