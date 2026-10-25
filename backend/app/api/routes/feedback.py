"""
NEXUS Feedback API Routes (Step 4.D.2)
Collects user ratings (+1/-1) and comments on assistant messages,
emitting learning signals and persisting feedback.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Conversation, Feedback, LearningSignal, Message, Run, User

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    message_id: str = Field(..., description="Target assistant message ID")
    rating: int = Field(..., ge=-1, le=1, description="Rating (+1 for up, -1 for down, 0 to remove)")
    comment: Optional[str] = Field(None, max_length=500, description="Optional feedback explanation")


@router.post("", status_code=status.HTTP_200_OK)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits user feedback (+1 / -1) with optional comment on an assistant message.
    Rating 0 removes/toggles off existing feedback.
    Strictly isolated to user's own conversations.
    """
    # 1. Verify message ownership & assistant role
    stmt = (
        select(Message, Conversation)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Message.id == payload.message_id, Conversation.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    msg, conv = row
    if msg.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted for assistant messages",
        )

    # 2. If rating is 0, delete feedback (toggle off)
    if payload.rating == 0:
        del_stmt = delete(Feedback).where(
            Feedback.message_id == payload.message_id,
            Feedback.user_id == current_user.id,
        )
        await db.execute(del_stmt)
        await db.commit()
        return {"status": "removed", "message_id": payload.message_id, "rating": 0}

    # 3. Upsert feedback
    fb_stmt = select(Feedback).where(
        Feedback.message_id == payload.message_id,
        Feedback.user_id == current_user.id,
    )
    fb_res = await db.execute(fb_stmt)
    existing_fb = fb_res.scalar_one_or_none()

    if existing_fb:
        existing_fb.rating = payload.rating
        existing_fb.comment = payload.comment
    else:
        new_fb = Feedback(
            message_id=payload.message_id,
            user_id=current_user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
        db.add(new_fb)

    # 4. Record learning signal
    # Attempt resolving latest run for conversation
    run_stmt = (
        select(Run)
        .where(Run.conversation_id == conv.id)
        .order_by(Run.created_at.desc())
        .limit(1)
    )
    run_res = await db.execute(run_stmt)
    latest_run = run_res.scalar_one_or_none()
    run_id = latest_run.id if latest_run else conv.id

    val = 1.0 if payload.rating > 0 else 0.0
    signal = LearningSignal(
        user_id=current_user.id,
        intent="conversation",
        strategy_key="response_quality",
        signal="user_feedback",
        value=val,
        source="feedback",
        run_id=run_id,
    )
    db.add(signal)

    await db.commit()
    return {"status": "saved", "message_id": payload.message_id, "rating": payload.rating}


@router.get("/{message_id}")
async def get_message_feedback(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves current user's feedback on a specific message."""
    fb_stmt = select(Feedback).where(
        Feedback.message_id == message_id,
        Feedback.user_id == current_user.id,
    )
    res = await db.execute(fb_stmt)
    fb = res.scalar_one_or_none()
    if not fb:
        return {"rating": 0, "comment": None}
    return {"rating": fb.rating, "comment": fb.comment}
