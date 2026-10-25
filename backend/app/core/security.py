"""
NEXUS Security & Cryptography (Step 1.D.2)
- Bcrypt password hashing (8..72 bytes validation)
- PyJWT encode/decode with strict 'type' validation ('access' vs 'refresh')
- Timing attack mitigation via dummy bcrypt compare
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import bcrypt
import jwt
from pydantic import ValidationError
from app.core.config import settings

# Precomputed dummy bcrypt hash for timing attack mitigation
DUMMY_BCRYPT_HASH = b"$2b$12$K1rFp5EaZ7B4Zt0Zz8Z7z.Z9Z8Z7z6Z5Z4Z3Z2Z1Z0Z9Z8Z7z6Z5"


class AuthSecurityError(Exception):
    pass


def validate_password_length(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) < 8 or len(encoded) > 72:
        raise ValueError("Password must be between 8 and 72 bytes in length.")
    return encoded


def hash_password(password: str) -> str:
    encoded = validate_password_length(password)
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(encoded, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        encoded_plain = plain_password.encode("utf-8")
        encoded_hash = hashed_password.encode("utf-8")
        return bcrypt.checkpw(encoded_plain, encoded_hash)
    except Exception:
        return False


def verify_dummy_password(plain_password: str) -> bool:
    """Executes a dummy hash check to equalize response time for non-existent users."""
    try:
        bcrypt.checkpw(plain_password.encode("utf-8"), DUMMY_BCRYPT_HASH)
    except Exception:
        pass
    return False


def create_token(
    user_id: str,
    token_type: str,  # 'access' or 'refresh'
    expires_delta: timedelta,
    extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str) -> str:
    return create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    )


def create_refresh_token(user_id: str) -> str:
    return create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_DAYS)
    )


def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """Decodes token and strictly validates that the token type matches expected_type."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != expected_type:
            raise AuthSecurityError(f"Invalid token type. Expected {expected_type}, received {payload.get('type')}.")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthSecurityError("Token has expired.")
    except jwt.InvalidTokenError as e:
        raise AuthSecurityError(f"Invalid token: {str(e)}")
