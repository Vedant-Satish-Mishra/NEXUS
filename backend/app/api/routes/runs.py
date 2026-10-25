"""
NEXUS Runs API Routes (Step 1.D.3, 2.D.2 & 4.D.2)
Manages run initiation, Server-Sent Event streaming, plan approvals, tool decisions, and workflow queries.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import check_rate_limit
from app.db.models import Run, RunEvent, User
from app.db.session import async_session_maker
from app.schemas.plan import PlanDecision
from app.schemas.run import RunCreate
from app.services.runs_service import RunsService, ToolDecision

router = APIRouter(prefix="/runs", tags=["runs"])
runs_service = RunsService(session_factory=async_session_maker)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Initiates a new reasoning run:
    - Enforces rate limit (6 runs/min per user)
    - Validates conversation ownership
    - Enforces 1 active run per user
    - Saves user message BEFORE generation
    - Auto-titles conversation from first prompt
    """
    check_rate_limit(current_user.id, "runs", limit=6, window_seconds=60)
    run = await runs_service.create_run(payload, current_user)
    return {"run_id": run.id}


@router.get("")
async def list_runs(
    status_filter: Optional[str] = Query(None, alias="status"),
    tier_filter: Optional[int] = Query(None, alias="tier"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists runs for the current user with filters and pagination for the Workflows page.
    """
    query = select(Run).where(Run.user_id == current_user.id)
    count_query = select(func.count(Run.id)).where(Run.user_id == current_user.id)

    if status_filter:
        query = query.where(Run.status == status_filter)
        count_query = count_query.where(Run.status == status_filter)
    if tier_filter:
        query = query.where(Run.tier == tier_filter)
        count_query = count_query.where(Run.tier == tier_filter)

    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(desc(Run.created_at)).offset((page - 1) * limit).limit(limit)
    res = await db.execute(query)
    runs = res.scalars().all()

    return {
        "items": [
            {
                "id": r.id,
                "conversation_id": r.conversation_id,
                "status": r.status,
                "tier": r.tier,
                "evaluation": r.evaluation,
                "retries": r.retries,
                "latency_ms": r.latency_ms,
                "created_at": r.created_at,
            }
            for r in runs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{run_id}/events")
async def stream_run_events_endpoint(
    run_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Streams Server-Sent Events for the specified run:
    - Emits queued, run_started, node_started, token*, node_finished, final
    - Periodic heartbeat
    - Cancels generation and persists partial answer if client disconnects
    """
    stmt = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return StreamingResponse(
        runs_service.execute_run_stream(run_id, current_user, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full run details and stored events for the Workflows page. 404 for other users' resources."""
    stmt = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Fetch stored events
    events_stmt = (
        select(RunEvent)
        .where(RunEvent.run_id == run_id)
        .order_by(RunEvent.seq)
    )
    e_res = await db.execute(events_stmt)
    events = e_res.scalars().all()

    return {
        "id": run.id,
        "conversation_id": run.conversation_id,
        "status": run.status,
        "tier": run.tier,
        "understanding": run.understanding,
        "plan": run.plan,
        "evaluation": run.evaluation,
        "retries": run.retries,
        "latency_ms": run.latency_ms,
        "created_at": run.created_at,
        "events": [
            {
                "seq": e.seq,
                "type": e.type,
                "payload": e.payload,
            }
            for e in events
        ],
    }


@router.post("/{run_id}/plan")
async def decide_plan_endpoint(
    run_id: str,
    decision: PlanDecision,
    current_user: User = Depends(get_current_user),
):
    """
    Submits user plan decision (approve, edit, replan) for an interrupted run.
    Returns 409 if run is not in awaiting_plan_approval state.
    """
    return await runs_service.decide_plan(run_id, decision, current_user)


@router.post("/{run_id}/tools/{tool_id}")
async def decide_tool_endpoint(
    run_id: str,
    tool_id: str,
    decision: ToolDecision,
    current_user: User = Depends(get_current_user),
):
    """
    Submits user decision for tool approval: approve, edit, or deny.
    Enforces rate limits (20 decisions/min).
    """
    check_rate_limit(current_user.id, "tool_decisions", limit=20, window_seconds=60)
    return await runs_service.decide_tool(run_id, tool_id, decision, current_user)


@router.post("/{run_id}/cancel")
async def cancel_run_endpoint(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancels an active or paused run."""
    return await runs_service.cancel_run(run_id, current_user)
