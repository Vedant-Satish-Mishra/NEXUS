"""
NEXUS Memory API Routes (Milestone 3)
Step 3.D.2 — Scoped user memory management, proposal decisions, and confirmation persistence.
"""

from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Memory, MemoryProposalRecord, User
from app.db.session import async_session_maker
from app.services.memory import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])
memory_service = MemoryService(session_factory=async_session_maker)


class MemoryOut(BaseModel):
    id: str
    kind: str
    content: str
    confirmed_at: str
    active: bool

    class Config:
        from_attributes = True


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    active: Optional[bool] = None


class ProposalOut(BaseModel):
    id: str
    run_id: str
    kind: str
    content: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


class ProposalDecision(BaseModel):
    action: Literal["accept", "edit", "reject"]
    content: Optional[str] = None


@router.get("", response_model=List[MemoryOut])
async def list_memories(
    kind: Optional[str] = None,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists confirmed memories for the current user."""
    stmt = select(Memory).where(Memory.user_id == current_user.id)
    if kind:
        stmt = stmt.where(Memory.kind == kind)
    if q:
        stmt = stmt.where(Memory.content.ilike(f"%{q}%"))

    stmt = stmt.order_by(Memory.confirmed_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        MemoryOut(
            id=m.id,
            kind=m.kind,
            content=m.content,
            confirmed_at=m.confirmed_at.isoformat(),
            active=m.active
        )
        for m in records
    ]


@router.patch("/{memory_id}", response_model=MemoryOut)
async def update_memory(
    memory_id: str,
    payload: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates confirmed memory content or active status."""
    stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == current_user.id)
    res = await db.execute(stmt)
    mem = res.scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    if payload.content is not None:
        mem.content = payload.content.strip()
    if payload.active is not None:
        mem.active = payload.active

    await db.commit()
    await db.refresh(mem)

    return MemoryOut(
        id=mem.id,
        kind=mem.kind,
        content=mem.content,
        confirmed_at=mem.confirmed_at.isoformat(),
        active=mem.active
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
):
    """Deletes memory from PostgreSQL and ChromaDB vector store."""
    deleted = await memory_service.delete_memory(current_user.id, memory_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def wipe_all_memories(
    current_user: User = Depends(get_current_user),
):
    """Wipes all confirmed memories for the current user."""
    await memory_service.wipe_all_memories(current_user.id)
    return None


@router.get("/proposals", response_model=List[ProposalOut])
async def list_proposals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists pending memory proposals for the current user."""
    stmt = (
        select(MemoryProposalRecord)
        .where(
            MemoryProposalRecord.user_id == current_user.id,
            MemoryProposalRecord.status == "pending"
        )
        .order_by(MemoryProposalRecord.created_at.desc())
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        ProposalOut(
            id=p.id,
            run_id=p.run_id,
            kind=p.kind,
            content=p.content,
            status=p.status,
            created_at=p.created_at.isoformat()
        )
        for p in records
    ]


@router.post("/proposals/{proposal_id}/decision")
async def decide_proposal_endpoint(
    proposal_id: str,
    decision: ProposalDecision,
    current_user: User = Depends(get_current_user),
):
    """
    Submits user confirmation decision for a memory proposal.
    Accepting or editing creates confirmed memory and vector; rejecting marks rejected.
    """
    res = await memory_service.decide_proposal(
        user_id=current_user.id,
        proposal_id=proposal_id,
        action=decision.action,
        content=decision.content
    )
    if res.get("status") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return res


@router.get("/graph")
async def get_memory_graph(
    current_user: User = Depends(get_current_user),
):
    """
    Returns graph nodes and edges for the current user's concepts and memories.
    """
    from app.services.graph_store import graph_store
    return await graph_store.get_user_graph(current_user.id)
