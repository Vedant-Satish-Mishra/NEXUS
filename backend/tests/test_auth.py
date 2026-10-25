"""
Unit & Integration Tests: Authentication & Security (Step 1.D.2)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import create_app
from app.db.models import Base
from app.db.session import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    AuthSecurityError
)


# Test in-memory SQLite database
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_test_session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with _test_session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_password_hashing():
    pwd = "secure_password_123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_token_type_enforcement():
    user_id = "usr_test_123"
    access_tok = create_access_token(user_id)
    refresh_tok = create_refresh_token(user_id)

    # Valid decoding
    acc_payload = decode_token(access_tok, expected_type="access")
    assert acc_payload["sub"] == user_id

    ref_payload = decode_token(refresh_tok, expected_type="refresh")
    assert ref_payload["sub"] == user_id

    # Cross-type rejection
    with pytest.raises(AuthSecurityError, match="Invalid token type"):
        decode_token(refresh_tok, expected_type="access")

    with pytest.raises(AuthSecurityError, match="Invalid token type"):
        decode_token(access_tok, expected_type="refresh")


@pytest.mark.asyncio
async def test_auth_full_journey():
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register
        reg_payload = {
            "name": "Arjun Sharma",
            "email": "arjun@example.com",
            "password": "strong_password_456"
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "arjun@example.com"
        assert "password" not in data
        assert "password_hash" not in data

        # Duplicate register should return 409
        dup_res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert dup_res.status_code == 409

        # 2. Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "arjun@example.com", "password": "strong_password_456"}
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data
        access_token = login_data["access_token"]
        assert "set-cookie" in login_res.headers

        # 3. Access protected /me route
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["name"] == "Arjun Sharma"

        # 4. Wrong password returns generic 401
        wrong_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "arjun@example.com", "password": "wrong_password"}
        )
        assert wrong_res.status_code == 401
        assert wrong_res.json()["detail"] == "Invalid email or password."
