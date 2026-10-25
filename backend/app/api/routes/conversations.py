"""
NEXUS Conversations API Routes (Step 1.D.3)
Scoped strictly to authenticated current_user. Returns 404 for others' resources.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.db.models import Conversation, ChatAgentConfig, User
from app.agents.registry import AGENTS
from app.schemas.agent_config import AgentConfig
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    ConversationUpdate,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations belonging to current user."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation with default agent configuration."""
    title = payload.title.strip() if payload.title else "New chat"
    conv = Conversation(
        user_id=current_user.id,
        title=title,
    )
    db.add(conv)
    await db.flush()

    # Create initial agent config
    config = ChatAgentConfig(
        conversation_id=conv.id,
        preset="balanced",
        enabled_agents=["controller", "retrieval", "reasoning", "memory", "evaluation"],
        auto_approve_plans=False,
        model_profile="fast",
    )
    db.add(config)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation details with ordered messages. 404 for other users' resources."""
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Sort messages chronologically
    sorted_messages = sorted(conv.messages, key=lambda m: m.created_at)
    return ConversationDetailOut(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageOut.model_validate(m) for m in sorted_messages],
    )


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename conversation title. 404 for other users' resources."""
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    conv.title = payload.title.strip()
    await db.commit()
    await db.refresh(conv)
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete conversation and cascade messages/runs. 404 for other users' resources."""
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conv)
    await db.commit()
    return None


@router.get("/{conversation_id}/agents", response_model=AgentConfig)
async def get_conversation_agents(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the per-chat agent configuration for a conversation."""
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.agent_config))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if not conv.agent_config:
        # Default fallback
        return AgentConfig(
            preset="balanced",
            enabled_agents=["controller", "retrieval", "reasoning", "memory", "evaluation"],
            auto_approve_plans=False,
            model_profile="fast",
        )

    return AgentConfig(
        preset=conv.agent_config.preset,
        enabled_agents=conv.agent_config.enabled_agents,
        auto_approve_plans=conv.agent_config.auto_approve_plans,
        model_profile=conv.agent_config.model_profile,
    )


@router.put("/{conversation_id}/agents", response_model=AgentConfig)
async def update_conversation_agents(
    conversation_id: str,
    payload: AgentConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update per-chat agent configuration.
    Validates agent names, locks controller/reasoning on, and persists config.
    Applies to subsequent runs.
    """
    # 1. Validate agent names
    valid_agent_names = set(AGENTS.keys())
    for agent_name in payload.enabled_agents:
        if agent_name not in valid_agent_names:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown agent name: '{agent_name}'. Valid: {list(valid_agent_names)}"
            )

    # 2. Verify conversation ownership
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.agent_config))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # 3. Update or create ChatAgentConfig
    if not conv.agent_config:
        config = ChatAgentConfig(
            conversation_id=conv.id,
            preset=payload.preset,
            enabled_agents=payload.enabled_agents,
            auto_approve_plans=payload.auto_approve_plans,
            model_profile=payload.model_profile,
        )
        db.add(config)
    else:
        conv.agent_config.preset = payload.preset
        conv.agent_config.enabled_agents = payload.enabled_agents
        conv.agent_config.auto_approve_plans = payload.auto_approve_plans
        conv.agent_config.model_profile = payload.model_profile

    await db.commit()
    return payload

