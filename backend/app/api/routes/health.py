"""
NEXUS Health Check Endpoint (Step 1.D.1)
Reports status of Database, ChromaDB, and Ollama with a 2-second timeout per probe.
Failures are reported in the response body rather than failing the 200 HTTP response.
"""
import asyncio
import os
from typing import Dict, Any
from fastapi import APIRouter
import httpx
from sqlalchemy import text
from app.core.config import settings
from app.db.session import async_session_maker

router = APIRouter(tags=["health"])


async def check_database() -> Dict[str, Any]:
    try:
        async with async_session_maker() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
            return {"status": "ok", "message": "Database responsive"}
    except Exception as e:
        return {"status": "down", "error": str(e)}


async def check_chroma() -> Dict[str, Any]:
    try:
        path = settings.CHROMA_PATH
        if os.path.exists(path) or os.path.exists(os.path.dirname(os.path.abspath(path))):
            return {"status": "ok", "path": path}
        return {"status": "degraded", "message": "Chroma directory initializing"}
    except Exception as e:
        return {"status": "down", "error": str(e)}


async def check_llm_servers() -> Dict[str, Any]:
    active_servers = []
    available_models = []

    async with httpx.AsyncClient(timeout=1.5) as client:
        # 1. Check Llamafile Qwen3 4B (port 8080)
        try:
            r4 = await client.get(f"{settings.QWEN3_4B_URL}/v1/models")
            if r4.status_code in (200, 404):
                active_servers.append("llamafile_4b (port 8080)")
                available_models.append("qwen3:4b")
        except Exception:
            pass

        # 2. Check Llamafile Qwen3 8B (port 8081)
        try:
            r8 = await client.get(f"{settings.QWEN3_8B_URL}/v1/models")
            if r8.status_code in (200, 404):
                active_servers.append("llamafile_8b (port 8081)")
                available_models.append("qwen3:8b")
        except Exception:
            pass

        # 3. Check Ollama (port 11434)
        try:
            ro = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if ro.status_code == 200:
                active_servers.append("ollama (port 11434)")
                for m in ro.json().get("models", []):
                    name = m.get("name")
                    if name and name not in available_models:
                        available_models.append(name)
        except Exception:
            pass

    if active_servers:
        return {
            "status": "ok",
            "active_servers": active_servers,
            "models": available_models,
        }
    return {
        "status": "down",
        "message": "Neither Llamafile (port 8080/8081) nor Ollama is reachable",
        "hint": f"Run 'run.bat' in {settings.LOCAL_QWEN_DIR}\\qwen 3 4b or qwen 3 8b",
    }


@router.get("/health")
async def health_check():
    db_res, chroma_res, llm_res = await asyncio.gather(
        check_database(),
        check_chroma(),
        check_llm_servers(),
        return_exceptions=True
    )

    db_data = db_res if isinstance(db_res, dict) else {"status": "error", "error": str(db_res)}
    chroma_data = chroma_res if isinstance(chroma_res, dict) else {"status": "error", "error": str(chroma_res)}
    llm_data = llm_res if isinstance(llm_res, dict) else {"status": "error", "error": str(llm_res)}

    overall_status = "ok" if (db_data.get("status") == "ok" and llm_data.get("status") == "ok") else "degraded"

    return {
        "status": overall_status,
        "services": {
            "database": db_data,
            "chroma": chroma_data,
            "llm": llm_data,
            "ollama": llm_data  # backwards compatibility
        }
    }
