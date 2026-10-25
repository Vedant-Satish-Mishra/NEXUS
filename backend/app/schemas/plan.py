"""
NEXUS Planner Schemas: PlanStep, Plan, and PlanDecision
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: str = Field(..., description="Unique step ID (e.g. step_1)")
    title: str = Field(..., description="Concise step title")
    detail: str = Field(..., description="Detailed instructions, milestones, or timeline")
    depends_on: List[str] = Field(default_factory=list, description="IDs of prerequisite steps")
    needs_retrieval: bool = Field(default=True, description="Whether this step requires retrieval")
    tool: Optional[str] = Field(None, description="Optional tool assigned to this step")


class Plan(BaseModel):
    goal: str = Field(..., description="High-level goal of the plan")
    steps: List[PlanStep] = Field(..., min_length=1, max_length=8, description="Ordered execution steps (1 to 8 steps)")


class PlanDecision(BaseModel):
    action: Literal["approve", "edit", "replan"] = Field(..., description="User's decision on the plan")
    steps: Optional[List[PlanStep]] = Field(None, description="User-modified steps when action='edit'")
    feedback: Optional[str] = Field(None, description="Critique or guidance when action='replan'")
    auto_approve_future: bool = Field(default=False, description="Whether to auto-approve subsequent plans in this chat")
