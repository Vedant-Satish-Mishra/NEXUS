"""
NEXUS Database Session & Engine Configuration
Async SQLAlchemy 2 engine with connection pooling and async session maker.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

# Engine configuration with connection recycling and pre-ping
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.ENV == "dev",
    future=True,
    pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for database session injection."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
