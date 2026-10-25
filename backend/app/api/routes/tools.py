"""
NEXUS Tools API Routes (Step 4.D.2)
Exposes registered tools metadata and audit execution history.
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Run, ToolExecution, User
from app.tools import executor

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_tools_metadata(current_user: User = Depends(get_current_user)):
    """
    Returns registered tools, description, and permission level for current user.
    """
    tools = executor.list_tools()
    result = []
    for t in tools:
        name = t["name"]
        if name == "web_search":
            perm = "disabled"
        elif t["requires_approval"]:
            perm = "needs_approval"
        else:
            perm = "auto"

        result.append(
            {
                "name": name,
                "description": t["description"],
                "requires_approval": t["requires_approval"],
                "timeout_s": t["timeout_s"],
                "permission": perm,
            }
        )
    return result


@router.get("/executions")
async def list_tool_executions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns history of tool executions for the current user's runs.
    """
    stmt = (
        select(ToolExecution)
        .join(Run, ToolExecution.run_id == Run.id)
        .where(Run.user_id == current_user.id)
        .order_by(desc(ToolExecution.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        {
            "id": r.id,
            "run_id": r.run_id,
            "tool": r.tool,
            "input": r.input,
            "output": r.output,
            "status": r.status,
            "approved_by_user": r.approved_by_user,
            "duration_ms": r.duration_ms,
            "created_at": r.created_at,
        }
        for r in records
    ]
