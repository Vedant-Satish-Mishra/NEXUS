"""
Shared Pytest Fixtures for NEXUS Test Suite
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.models import Base, User
from app.api.deps import get_db
from app.main import create_app
from app.api.routes.runs import runs_service
from app.api.routes.files import file_service
from app.api.routes.memory import memory_service
from app.core.security import hash_password, create_access_token


class MockLLMProvider:
    async def chat(self, messages, **opts):
        return "Mock response"

    async def stream(self, messages, **opts):
        for token in ["Mock", " ", "response", "!"]:
            yield token

    async def structured(self, model, **opts):
        if hasattr(model, "__fields__") or hasattr(model, "model_fields"):
            return model.model_construct()
        return model()

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
async def client(test_db, monkeypatch):
    app = create_app()

    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(runs_service, "session_factory", test_db)
    monkeypatch.setattr(file_service, "session_factory", test_db)
    monkeypatch.setattr(memory_service, "session_factory", test_db)

    # Monkeypatch default llm provider in app.agents.graph
    from app.agents import graph as agent_graph
    monkeypatch.setattr(agent_graph, "default_llm_provider", MockLLMProvider())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
