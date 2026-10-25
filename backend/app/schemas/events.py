"""
NEXUS Server-Sent Events (SSE) Protocol (Discriminated Union on 'type')
"""
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from .understanding import Understanding
from .plan import Plan
from .run import MemoryProposal


class QueuedEvent(BaseModel):
    type: Literal["queued"] = "queued"
    position: int = Field(..., description="Position in the GPU worker queue")


class RunStartedEvent(BaseModel):
    type: Literal["run_started"] = "run_started"
    run_id: str
    tier: int = Field(..., ge=1, le=3)
    enabled_agents: List[str]


class NodeStartedEvent(BaseModel):
    type: Literal["node_started"] = "node_started"
    node: str = Field(..., description="Agent or pipeline node name")


class NodeFinishedEvent(BaseModel):
    type: Literal["node_finished"] = "node_finished"
    node: str
    summary: str
    ms: int
    status: Literal["ok", "skipped", "error"] = "ok"


class UnderstandingEvent(BaseModel):
    type: Literal["understanding"] = "understanding"
    understanding: Understanding


class PlanProposedEvent(BaseModel):
    type: Literal["plan_proposed"] = "plan_proposed"
    run_id: str
    plan: Plan
    requires_approval: bool = True


class CitationItem(BaseModel):
    file: str
    page: int
    score: float
    chunk_id: str
    snippet: Optional[str] = None


class SourcesEvent(BaseModel):
    type: Literal["sources"] = "sources"
    sources: List[CitationItem]


class ToolProposedEvent(BaseModel):
    type: Literal["tool_proposed"] = "tool_proposed"
    tool_id: str
    tool: str
    input: str
    requires_approval: bool = True


class ToolResultEvent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_id: str
    tool: str
    output: str
    ms: int
    status: Literal["ok", "denied", "error"]


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    content: str


class EvaluationEvent(BaseModel):
    type: Literal["evaluation"] = "evaluation"
    score: float
    checks: Dict[str, bool]
    retry: bool = False
    critique: Optional[str] = None


class MemoryProposalEvent(BaseModel):
    type: Literal["memory_proposal"] = "memory_proposal"
    proposals: List[MemoryProposal]


class FinalEvent(BaseModel):
    type: Literal["final"] = "final"
    message_id: str
    content: str
    citations: List[CitationItem] = Field(default_factory=list)


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


class HeartbeatEvent(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"
    timestamp: int


class AgentHintEvent(BaseModel):
    type: Literal["agent_hint"] = "agent_hint"
    agent: str
    reason: str


SSEEvent = Annotated[
    Union[
        QueuedEvent,
        RunStartedEvent,
        NodeStartedEvent,
        NodeFinishedEvent,
        UnderstandingEvent,
        PlanProposedEvent,
        SourcesEvent,
        ToolProposedEvent,
        ToolResultEvent,
        TokenEvent,
        EvaluationEvent,
        MemoryProposalEvent,
        FinalEvent,
        ErrorEvent,
        HeartbeatEvent,
        AgentHintEvent
    ],
    Field(discriminator="type")
]
