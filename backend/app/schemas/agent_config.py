"""
NEXUS Agent Configuration & Presets
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class AgentConfig(BaseModel):
    preset: Literal["fast", "balanced", "full", "custom"] = Field(default="balanced")
    enabled_agents: List[str] = Field(
        default_factory=lambda: ["controller", "retrieval", "reasoning", "memory", "evaluation"],
        description="Active agent list. Controller and reasoning are strictly enforced."
    )
    auto_approve_plans: bool = Field(default=False, description="Skip plan approval wait")
    model_profile: Literal["fast", "quality"] = Field(default="fast", description="Qwen3 4B vs 8B Q4")

    @model_validator(mode="after")
    def enforce_required_agents(self) -> "AgentConfig":
        """Controller and Reasoning are locked on and can never be disabled."""
        agents = set(self.enabled_agents)
        agents.add("controller")
        agents.add("reasoning")
        self.enabled_agents = list(agents)
        return self
