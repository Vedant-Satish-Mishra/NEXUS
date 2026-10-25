"""
NEXUS Core Schemas: Principal & Identity
"""
from pydantic import BaseModel, Field


class Principal(BaseModel):
    user_id: str = Field(..., description="Unique authenticated user ID")
    conversation_id: str | None = Field(default=None, description="Active conversation ID if within a chat scope")
