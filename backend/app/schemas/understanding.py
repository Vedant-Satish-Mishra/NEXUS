"""
NEXUS Understanding Schema (Pydantic v2)
Structured query analysis output
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Understanding(BaseModel):
    intent: str = Field(..., description="Classified intent (e.g. placement_preparation, code_debugging)")
    domain: Optional[str] = Field(None, description="Primary technical domain (e.g. Java, DSA, DBMS)")
    user_context: Dict[str, str] = Field(default_factory=dict, description="Extracted context: year, branch, time_available")
    requirements: List[str] = Field(default_factory=list, description="Decomposed tasks/milestones")
    output_type: str = Field(default="answer", description="Format expectation (e.g. study_plan, code_snippet, explanation)")
    complexity: Literal["simple", "document", "complex"] = Field(default="simple", description="Estimated task complexity")
    needs_retrieval: bool = Field(default=False, description="Whether local document evidence is required")
    needs_plan: bool = Field(default=False, description="Whether multi-step planner approval is required")
    tools_required: List[Literal["calculator", "python", "file_reader", "local_search", "web_search"]] = Field(
        default_factory=list,
        description="Allow-listed tools requested"
    )
    constraints: List[str] = Field(default_factory=list, description="Time, platform, or library constraints")
    privacy_mode: Literal["local_only", "web_allowed"] = Field(default="local_only", description="Data privacy constraint")
