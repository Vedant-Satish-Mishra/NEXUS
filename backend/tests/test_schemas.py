"""
Unit Tests: NEXUS Schemas & SSE Event Protocol (Step 0.4)
Validates Pydantic v2 serialization and round-trip deserialization for all events.
"""

import pytest
from app.schemas.core import Principal
from app.schemas.understanding import Understanding
from app.schemas.plan import Plan, PlanStep, PlanDecision
from app.schemas.agent_config import AgentConfig
from app.schemas.run import RunCreate, FileOut, MemoryProposal, ToolProposal
from app.schemas.events import (
    QueuedEvent,
    RunStartedEvent,
    NodeStartedEvent,
    NodeFinishedEvent,
    UnderstandingEvent,
    PlanProposedEvent,
    CitationItem,
    SourcesEvent,
    ToolProposedEvent,
    ToolResultEvent,
    TokenEvent,
    EvaluationEvent,
    MemoryProposalEvent,
    FinalEvent,
    ErrorEvent,
    HeartbeatEvent,
    AgentHintEvent,
    SSEEvent
)
from pydantic import TypeAdapter


def test_principal_schema():
    p = Principal(user_id="usr_123", conversation_id="conv_abc")
    assert p.user_id == "usr_123"
    assert p.conversation_id == "conv_abc"


def test_agent_config_enforcement():
    # Controller and reasoning can never be removed
    cfg = AgentConfig(preset="fast", enabled_agents=["retrieval"])
    assert "controller" in cfg.enabled_agents
    assert "reasoning" in cfg.enabled_agents
    assert "retrieval" in cfg.enabled_agents


def test_understanding_schema():
    und = Understanding(
        intent="placement_preparation",
        domain="Java",
        user_context={"year": "4th Year"},
        requirements=["Core Java", "DSA"],
        output_type="roadmap",
        complexity="complex",
        needs_retrieval=True,
        needs_plan=True
    )
    dumped = und.model_dump()
    loaded = Understanding.model_validate(dumped)
    assert loaded.intent == "placement_preparation"
    assert loaded.complexity == "complex"


def test_plan_and_decision_schema():
    step1 = PlanStep(id="st_1", title="Foundations", detail="Learn Java syntax")
    plan = Plan(goal="Master Java", steps=[step1])
    assert len(plan.steps) == 1

    dec = PlanDecision(action="approve", auto_approve_future=True)
    assert dec.action == "approve"
    assert dec.auto_approve_future is True


def test_sse_events_round_trip():
    adapter = TypeAdapter(SSEEvent)

    events = [
        QueuedEvent(position=1),
        RunStartedEvent(run_id="r1", tier=3, enabled_agents=["controller", "reasoning"]),
        NodeStartedEvent(node="understanding"),
        NodeFinishedEvent(node="understanding", summary="Extracted", ms=120, status="ok"),
        UnderstandingEvent(
            understanding=Understanding(
                intent="qa",
                requirements=["explain JVM"],
                complexity="simple",
                needs_retrieval=False,
                needs_plan=False
            )
        ),
        PlanProposedEvent(
            run_id="r1",
            plan=Plan(
                goal="Goal",
                steps=[PlanStep(id="s1", title="Step 1", detail="Details")]
            ),
            requires_approval=True
        ),
        SourcesEvent(
            sources=[CitationItem(file="notes.md", page=1, score=0.9, chunk_id="c1")]
        ),
        ToolProposedEvent(tool_id="t1", tool="python", input="print(1)", requires_approval=True),
        ToolResultEvent(tool_id="t1", tool="python", output="1", ms=45, status="ok"),
        TokenEvent(content="Hello "),
        EvaluationEvent(score=0.95, checks={"citation_valid": True}, retry=False),
        MemoryProposalEvent(
            proposals=[MemoryProposal(id="m1", kind="long_term", content="Prefers Java")]
        ),
        FinalEvent(message_id="msg_01", content="Done", citations=[]),
        AgentHintEvent(agent="planner", reason="Task has multiple steps"),
        HeartbeatEvent(timestamp=1700000000),
        ErrorEvent(code="model_unavailable", message="Ollama is unreachable")
    ]

    for evt in events:
        json_data = evt.model_dump(mode="json")
        deserialized = adapter.validate_python(json_data)
        assert deserialized.type == evt.type
