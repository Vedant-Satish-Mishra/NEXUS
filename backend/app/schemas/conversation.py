"""
NEXUS Conversation and Message Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default="New chat", description="Initial conversation title")


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="New title")


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: List[MessageOut] = Field(default_factory=list)
