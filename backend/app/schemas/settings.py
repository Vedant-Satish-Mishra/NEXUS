from typing import Literal
from pydantic import BaseModel, Field

class UserSettingsSchema(BaseModel):
    model_profile: Literal["fast", "quality"] = "fast"
    default_preset: Literal["fast", "balanced", "full"] = "balanced"
    memory_enabled: bool = True
    learning_enabled: bool = True
    privacy_mode: bool = True
    web_search_enabled: bool = False
    theme: str = "system"
    reduced_motion: bool = False

class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, description="User password for confirmation")
