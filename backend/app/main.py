"""
NEXUS FastAPI Application Factory (Step 1.D.1 & Milestone 4)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, RequestIdMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.runs import router as runs_router
from app.api.routes.files import router as files_router, file_service
from app.api.routes.memory import router as memory_router
from app.api.routes.tools import router as tools_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.settings import router as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Setup logging
    setup_logging()
    file_service.start_worker()
    
    # Auto-initialize local tables when using SQLite
    if "sqlite" in settings.DATABASE_URL:
        import os
        from app.db.models import Base
        from app.db.session import engine
        os.makedirs("./data", exist_ok=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield
    # Shutdown: Close background worker
    await file_service.stop_worker()


def create_app() -> FastAPI:
    app = FastAPI(
        title="NEXUS AI Cognitive System",
        version="1.0.0",
        description="Local-first multi-agent cognitive architecture with deterministic tier routing.",
        lifespan=lifespan
    )

    # Middleware
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )

    # Mount API routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(conversations_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")
    app.include_router(files_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(tools_router, prefix="/api/v1")
    app.include_router(feedback_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")

    return app


app = create_app()
