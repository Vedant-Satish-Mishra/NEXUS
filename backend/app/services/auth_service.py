"""
NEXUS Authentication Service (Step 1.D.2)
Handles user registration, credential verification, and token rotation.
"""
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    hash_password,
    verify_password,
    verify_dummy_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.db.models import User, UserSettings
from app.schemas.auth import UserRegister, UserLogin, UserOut


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email.lower().strip())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, req: UserRegister) -> User:
    existing = await get_user_by_email(session, req.email)
    if existing:
        raise UserAlreadyExistsError(f"User with email '{req.email}' already exists.")

    password_hash = hash_password(req.password)
    user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        password_hash=password_hash
    )
    session.add(user)
    await session.flush()

    # Initialize default settings for user
    settings_record = UserSettings(user_id=user.id)
    session.add(settings_record)
    await session.commit()
    await session.refresh(user)

    return user


async def authenticate_user(session: AsyncSession, req: UserLogin) -> Tuple[User, str, str]:
    user = await get_user_by_email(session, req.email)
    if not user:
        verify_dummy_password(req.password)
        raise InvalidCredentialsError("Invalid email or password.")

    if not verify_password(req.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return user, access_token, refresh_token


async def refresh_user_tokens(session: AsyncSession, refresh_token: str) -> Tuple[User, str, str]:
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidCredentialsError("Invalid refresh token claims.")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise InvalidCredentialsError("User account no longer exists.")

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return user, new_access_token, new_refresh_token
