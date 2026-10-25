"""
NEXUS Dashboard API (Step 5.D.1)
Provides aggregated metrics via SQL only (no heavy client-side computations):
- Runs per day (14 days) by tier
- Average latency by tier
- Evaluation score trend
- Thumbs up/down feedback ratio
- Files and chunks count
- Memories count
- Recent tasks
- Live services health
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import asyncio
import os
import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.db.models import (
    Conversation,
    Feedback,
    FileRecord,
    LearningSignal,
    Memory,
    Message,
    Run,
    User,
)
from app.schemas.dashboard import (
    DashboardData,
    EvalScorePoint,
    FeedbackRatio,
    RecentTask,
    RunsPerDayPoint,
    ServicesHealth,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _probe_services() -> ServicesHealth:
    ollama_ok = False
    sandbox_ok = False
    db_ok = True
    chroma_ok = os.path.exists(settings.CHROMA_PATH) or os.path.exists(os.path.dirname(os.path.abspath(settings.CHROMA_PATH)))

    async with httpx.AsyncClient(timeout=1.0) as client:
        # Check LLM / Ollama
        try:
            r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                ollama_ok = True
        except Exception:
            try:
                r2 = await client.get(f"{settings.QWEN3_4B_URL}/v1/models")
                if r2.status_code in (200, 404):
                    ollama_ok = True
            except Exception:
                ollama_ok = False

        # Check Sandbox
        try:
            r = await client.get(f"{settings.SANDBOX_URL}/health")
            if r.status_code == 200:
                sandbox_ok = True
        except Exception:
            sandbox_ok = False

    return ServicesHealth(
        ollama=ollama_ok,
        db=db_ok,
        chroma=chroma_ok,
        sandbox=sandbox_ok,
    )


@router.get("", response_model=DashboardData, status_code=status.HTTP_200_OK)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardData:
    """
    Returns aggregated analytics strictly scoped to current user.
    All data is computed via SQL aggregations.
    """
    now = datetime.now(timezone.utc)
    today = now.date()
    start_date = today - timedelta(days=13)
    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)

    # 1. Runs per day (last 14 days)
    runs_stmt = (
        select(Run)
        .where(Run.user_id == current_user.id, Run.created_at >= start_dt)
        .order_by(Run.created_at.asc())
    )
    res_runs = await db.execute(runs_stmt)
    all_recent_runs = res_runs.scalars().all()

    # Pre-populate 14 days
    date_map: Dict[str, Dict[str, int]] = {}
    for i in range(14):
        d_str = (start_date + timedelta(days=i)).isoformat()
        date_map[d_str] = {"count": 0, "tier1": 0, "tier2": 0, "tier3": 0}

    for r in all_recent_runs:
        d_str = r.created_at.date().isoformat()
        if d_str in date_map:
            date_map[d_str]["count"] += 1
            if r.tier == 1:
                date_map[d_str]["tier1"] += 1
            elif r.tier == 2:
                date_map[d_str]["tier2"] += 1
            elif r.tier == 3:
                date_map[d_str]["tier3"] += 1

    runs_per_day = [
        RunsPerDayPoint(
            date=k,
            count=v["count"],
            tier1=v["tier1"],
            tier2=v["tier2"],
            tier3=v["tier3"],
        )
        for k, v in date_map.items()
    ]

    # 2. Average latency by tier
    lat_stmt = (
        select(Run.tier, func.avg(Run.latency_ms))
        .where(Run.user_id == current_user.id, Run.latency_ms.isnot(None))
        .group_by(Run.tier)
    )
    lat_res = await db.execute(lat_stmt)
    avg_latency_by_tier = {f"tier{row[0]}": round(float(row[1] or 0), 1) for row in lat_res.all()}
    for t in ["tier1", "tier2", "tier3"]:
        if t not in avg_latency_by_tier:
            avg_latency_by_tier[t] = 0.0

    # 3. Evaluation score trend
    eval_stmt = (
        select(
            func.date(LearningSignal.created_at).label("d"),
            func.avg(LearningSignal.value)
        )
        .where(
            LearningSignal.user_id == current_user.id,
            LearningSignal.source == "evaluation",
            LearningSignal.created_at >= start_dt
        )
        .group_by(func.date(LearningSignal.created_at))
        .order_by(func.date(LearningSignal.created_at).asc())
    )
    try:
        eval_res = await db.execute(eval_stmt)
        eval_trend = [
            EvalScorePoint(date=str(row[0]), avg_score=round(float(row[1]), 2))
            for row in eval_res.all()
        ]
    except Exception:
        eval_trend = []

    # 4. Feedback ratio
    fb_stmt = (
        select(Feedback.rating, func.count(Feedback.id))
        .join(Message, Feedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == current_user.id)
        .group_by(Feedback.rating)
    )
    fb_res = await db.execute(fb_stmt)
    up = 0
    down = 0
    for r_val, c_count in fb_res.all():
        if r_val > 0:
            up += c_count
        elif r_val < 0:
            down += c_count
    total_fb = up + down
    ratio = round((up / total_fb), 2) if total_fb > 0 else 1.0
    feedback_ratio = FeedbackRatio(up=up, down=down, ratio=ratio)

    # 5. Files and Chunks count
    file_stmt = select(
        func.count(FileRecord.id),
        func.coalesce(func.sum(FileRecord.chunks), 0)
    ).where(FileRecord.user_id == current_user.id)
    f_res = await db.execute(file_stmt)
    f_row = f_res.first()
    files_count = int(f_row[0]) if f_row else 0
    chunks_count = int(f_row[1]) if f_row else 0

    # 6. Memories count
    mem_stmt = select(func.count(Memory.id)).where(Memory.user_id == current_user.id)
    m_res = await db.execute(mem_stmt)
    memories_count = int(m_res.scalar() or 0)

    # 7. Recent Tasks (top 5 runs)
    recent_stmt = (
        select(Run)
        .where(Run.user_id == current_user.id)
        .order_by(desc(Run.created_at))
        .limit(5)
    )
    recent_res = await db.execute(recent_stmt)
    recent_runs = recent_res.scalars().all()

    recent_tasks = []
    for r in recent_runs:
        # Get first user prompt
        prompt_text = "Task execution"
        msg_stmt = (
            select(Message.content)
            .where(Message.conversation_id == r.conversation_id, Message.role == "user")
            .order_by(Message.created_at.asc())
            .limit(1)
        )
        msg_res = await db.execute(msg_stmt)
        p = msg_res.scalar_one_or_none()
        if p:
            prompt_text = p[:80] + ("..." if len(p) > 80 else "")

        recent_tasks.append(
            RecentTask(
                run_id=r.id,
                conversation_id=r.conversation_id,
                prompt=prompt_text,
                tier=r.tier,
                status=r.status,
                duration_ms=r.latency_ms,
                created_at=r.created_at.isoformat(),
            )
        )

    # 8. Probe services
    services_health = await _probe_services()

    return DashboardData(
        runs_per_day=runs_per_day,
        avg_latency_by_tier=avg_latency_by_tier,
        evaluation_score_trend=eval_trend,
        feedback_ratio=feedback_ratio,
        files_count=files_count,
        chunks_count=chunks_count,
        memories_count=memories_count,
        recent_tasks=recent_tasks,
        services_health=services_health,
    )
