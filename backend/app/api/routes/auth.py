"""
NEXUS Authentication Routes (Step 1.D.2)
- /auth/register
- /auth/login
- /auth/refresh
- /auth/logout
- /auth/me
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_user,
    get_db,
    login_rate_limiter,
    register_rate_limiter,
)
from app.core.config import settings
from app.db.models import User
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from app.services.auth_service import (
    authenticate_user,
    refresh_user_tokens,
    register_user,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="nexus_refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENV != "dev",
        path="/api/v1/auth",
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 3600
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    req: UserRegister,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    register_rate_limiter.check(client_ip)

    try:
        user = await register_user(session, req)
        return UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: UserLogin,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    login_rate_limiter.check(client_ip)

    try:
        user, access_token, refresh_token = await authenticate_user(session, req)
        set_refresh_cookie(response, refresh_token)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserOut(
                id=user.id,
                name=user.name,
                email=user.email,
                created_at=user.created_at
            )
        )
    except InvalidCredentialsError:
        # Generic 401 error message for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_route(
    request: Request,
    response: Response,
    nexus_refresh_token: str = Cookie(None),
    session: AsyncSession = Depends(get_db)
):
    # Support cookie or Authorization Bearer header for refresh
    token = nexus_refresh_token
    if not token and request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing."
        )

    try:
        user, new_access_token, new_refresh_token = await refresh_user_tokens(session, token)
        set_refresh_cookie(response, new_refresh_token)
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            user=UserOut(
                id=user.id,
                name=user.name,
                email=user.email,
                created_at=user.created_at
            )
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key="nexus_refresh_token", path="/api/v1/auth")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at
    )
