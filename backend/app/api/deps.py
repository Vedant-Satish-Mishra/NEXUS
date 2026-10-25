"""
NEXUS FastAPI Dependencies & Security Guards (Step 1.D.2)
Provides current user verification, ownership authorization, and in-memory rate limiting.
"""

import time
from collections import defaultdict
from typing import AsyncGenerator, Dict, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, AuthSecurityError
from app.db.models import User, Conversation
from app.db.session import get_db
from app.schemas.core import Principal
from app.services.auth_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


# In-memory sliding window rate limiter
class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int):
        self.rpm = requests_per_minute
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, key: str):
        now = time.time()
        window_start = now - 60.0
        # Prune older entries
        self.history[key] = [t for t in self.history[key] if t > window_start]
        if len(self.history[key]) >= self.rpm:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.rpm} requests per minute."
            )
        self.history[key].append(now)


login_rate_limiter = InMemoryRateLimiter(requests_per_minute=5)
register_rate_limiter = InMemoryRateLimiter(requests_per_minute=3)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db)
) -> User:
    if auth and auth.credentials:
        try:
            payload = decode_token(auth.credentials, expected_type="access")
            user_id = payload.get("sub")
            if user_id:
                user = await get_user_by_id(session, user_id)
                if user:
                    return user
        except AuthSecurityError as e:
            if settings.ENV != "dev":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e)
                )

    # In dev environment, provide seamless dev user fallback
    if settings.ENV == "dev":
        from app.services.auth_service import get_user_by_email, register_user
        from app.schemas.auth import UserRegister
        dev_email = "dev@example.com"
        dev_user = await get_user_by_email(session, dev_email)
        if not dev_user:
            dev_user = await register_user(
                session,
                UserRegister(name="Dev User", email=dev_email, password="nexusdevpassword123")
            )
        return dev_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials were not provided."
    )


class PrincipalGuard:
    """Verifies that conversation_id belongs to the current user (404 otherwise)."""
    def __init__(self, conversation_param: str = "conversation_id"):
        self.conversation_param = conversation_param

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db)
    ) -> Principal:
        conv_id = request.path_params.get(self.conversation_param) or request.query_params.get(self.conversation_param)
        if not conv_id:
            # Fallback to body if POST request
            return Principal(user_id=current_user.id, conversation_id="default")

        stmt = select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id
        )
        result = await session.execute(stmt)
        conv = result.scalar_one_or_none()

        if not conv:
            # Always return 404 for resources not owned to prevent user enumeration
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found."
            )

        return Principal(user_id=current_user.id, conversation_id=conv_id)


get_principal = PrincipalGuard()
