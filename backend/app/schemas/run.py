"""
NEXUS Run Request & Resource Response Schemas
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    conversation_id: str = Field(..., description="Target conversation ID")
    message: str = Field(..., min_length=1, description="User prompt text")
    file_ids: List[str] = Field(default_factory=list, description="IDs of uploaded files attached to this run")


class FileOut(BaseModel):
    id: str
    filename: str
    mime: str
    size: int
    scope: Literal["chat", "personal", "system"]
    status: Literal["uploaded", "processing", "ready", "failed"]
    pages: int = 0
    chunks: int = 0
    error: Optional[str] = None


class MemoryProposal(BaseModel):
    id: str
    kind: Literal["long_term", "episodic"]
    content: str
    status: Literal["pending", "accepted", "edited", "rejected"] = "pending"
    importance: Literal["high", "medium", "low"] = "medium"


class ToolProposal(BaseModel):
    tool: str
    input: str
    requires_approval: bool = True
    reason: Optional[str] = None
