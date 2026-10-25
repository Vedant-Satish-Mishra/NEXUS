"""
NEXUS LangGraph Checkpointer Management (Step 1.B.2)
Provides an async context manager for AsyncPostgresSaver lifecycle,
kept open for the FastAPI lifespan. Falls back to MemorySaver if PostgreSQL
is unavailable in standalone test environments.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings

logger = logging.getLogger("nexus.agents.checkpointer")


@asynccontextmanager
async def get_checkpointer(dsn: Optional[str] = None) -> AsyncIterator[BaseCheckpointSaver]:
    """
    Creates and yields an active checkpointer instance.
    Runs checkpointer.setup() on connection to ensure schema tables exist.
    """
    conn_str = dsn or settings.CHECKPOINT_DSN
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        async with AsyncPostgresSaver.from_conn_string(conn_str) as saver:
            await saver.setup()
            logger.info("Connected to Postgres checkpointer successfully.")
            yield saver
    except Exception as exc:
        logger.warning(
            "Could not initialize AsyncPostgresSaver (%s). Falling back to MemorySaver.",
            exc,
        )
        yield MemorySaver()
