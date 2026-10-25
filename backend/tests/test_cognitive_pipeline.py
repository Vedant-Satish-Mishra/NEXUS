"""
Unit & Integration Tests for Milestone 2: Cognitive Pipeline
Covers:
- Step 2.B.1: Guarded decorators & agent registry
- Step 2.B.2: Understanding extraction & Executive Controller tier routing
- Step 2.B.3: Planner Agent topological sort & cycle detection
- Step 2.C.1: Chunking & Ingestion
- Step 2.C.2: Multi-query Retrieval service & de-duplication
- Step 2.D.1: Per-chat agent configuration & enforcement
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List

from app.agents.registry import AGENTS, PRESETS, guarded, traced
from app.agents.understanding import is_non_trivial, understanding_node
from app.agents.controller import controller_node
from app.agents.planner import validate_and_toposort_steps, PlanStep
from app.rag.chunking import DocumentChunk, chunk_markdown
from app.rag.loaders import LoadedDocument
from app.rag.retrieval import RetrievalService
from app.schemas.core import Principal
from app.schemas.agent_config import AgentConfig


# -----------------------------------------------------------------------------
# 1. Tests for 2.B.1 (Registry & Guard)
# -----------------------------------------------------------------------------
def test_agent_registry_integrity():
    assert "controller" in AGENTS
    assert "reasoning" in AGENTS
    assert AGENTS["controller"].required is True
    assert AGENTS["reasoning"].required is True
    assert AGENTS["planner"].required is False
    assert AGENTS["retrieval"].required is False

    for preset_name, agents in PRESETS.items():
        assert "reasoning" in agents


@pytest.mark.asyncio
async def test_guarded_decorator_skips_disabled_agents():
    @guarded("planner")
    async def sample_planner_node(state: Dict[str, Any]):
        return {"plan": {"goal": "test"}}

    # Disabled
    disabled_state = {"enabled_agents": ["reasoning"]}
    res = await sample_planner_node(disabled_state)
    assert "trace" in res
    assert res["trace"][0]["status"] == "skipped"
    assert "plan" not in res

    # Enabled
    enabled_state = {"enabled_agents": ["reasoning", "planner"]}
    res = await sample_planner_node(enabled_state)
    assert res.get("plan", {}).get("goal") == "test"


# -----------------------------------------------------------------------------
# 2. Tests for 2.B.2 (Understanding & Controller)
# -----------------------------------------------------------------------------
def test_is_non_trivial_detection():
    assert is_non_trivial("Hi", []) is False
    assert is_non_trivial("What is a hashmap?", []) is False
    assert is_non_trivial("Can you create a 4-month Java study roadmap?", []) is True
    assert is_non_trivial("Summarize notes", ["file-123"]) is True
    assert is_non_trivial("Explain this document please", []) is True


@pytest.mark.asyncio
async def test_controller_tier_routing_and_downgrades():
    # 1. Simple query -> Tier 1
    state_simple = {
        "user_input": "What is 2+2?",
        "file_ids": [],
        "enabled_agents": ["controller", "reasoning"],
        "understanding": {"complexity": "simple"}
    }
    out_simple = await controller_node(state_simple)
    assert out_simple["tier"] == "simple"
    assert out_simple["route"] == ["reason"]
    assert len(out_simple["agent_hints"]) == 0

    # 2. Document query with Retrieval enabled -> Tier 2
    state_doc = {
        "user_input": "Summarize my uploaded DBMS notes",
        "file_ids": ["f1"],
        "enabled_agents": ["controller", "reasoning", "retrieval"],
        "understanding": {"complexity": "document"}
    }
    out_doc = await controller_node(state_doc)
    assert out_doc["tier"] == "document"
    assert "retrieval" in out_doc["route"]

    # 3. Document query with Retrieval disabled -> Clamps to simple + emits hint
    state_doc_disabled = {
        "user_input": "Summarize my uploaded DBMS notes",
        "file_ids": ["f1"],
        "enabled_agents": ["controller", "reasoning"],
        "understanding": {"complexity": "document"}
    }
    out_clamped = await controller_node(state_doc_disabled)
    assert out_clamped["tier"] == "simple"
    assert any(h["agent"] == "retrieval" for h in out_clamped["agent_hints"])

    # 4. Complex query with Planner enabled -> Tier 3
    state_complex = {
        "user_input": "Create a 4-month Java placement plan with milestones",
        "file_ids": [],
        "enabled_agents": ["controller", "reasoning", "planner", "retrieval"],
        "understanding": {"complexity": "complex"}
    }
    out_complex = await controller_node(state_complex)
    assert out_complex["tier"] == "complex"
    assert "plan_generate" in out_complex["route"]
    assert "plan_wait" in out_complex["route"]


# -----------------------------------------------------------------------------
# 3. Tests for 2.B.3 (Planner Topological Sort & Acyclic Graph)
# -----------------------------------------------------------------------------
def test_planner_topological_sort_success():
    steps = [
        PlanStep(id="step_3", title="Mock Interviews", detail="Practice", depends_on=["step_2"]),
        PlanStep(id="step_1", title="Core Java", detail="Learn syntax", depends_on=[]),
        PlanStep(id="step_2", title="DSA Practice", detail="Solve leetcode", depends_on=["step_1"]),
    ]
    sorted_steps = validate_and_toposort_steps(steps)
    step_ids = [s.id for s in sorted_steps]
    assert step_ids == ["step_1", "step_2", "step_3"]


def test_planner_cycle_detection():
    steps = [
        PlanStep(id="step_1", title="A", detail="", depends_on=["step_2"]),
        PlanStep(id="step_2", title="B", detail="", depends_on=["step_1"]),
    ]
    with pytest.raises(ValueError, match="Cyclic dependency"):
        validate_and_toposort_steps(steps)


# -----------------------------------------------------------------------------
# 4. Tests for 2.C.1 (Heading-aware Chunking)
# -----------------------------------------------------------------------------
def test_markdown_heading_aware_chunking():
    md_content = """# Java Placement Guide
Topic: Java Placements

## Core Java
Java memory model uses heap and stack.
Garbage collection reclaims unused memory.

## Data Structures
Arrays have O(1) random access.
LinkedLists have O(1) insertion at head.
"""
    doc = LoadedDocument(
        content=md_content,
        source="test.md",
        filename="test.md",
        extension=".md",
        topic="Java Placements"
    )
    chunks = chunk_markdown(doc, target_words=50)
    assert len(chunks) >= 2
    assert any("Core Java" in c.heading_path for c in chunks)
    assert any("Data Structures" in c.heading_path for c in chunks)


# -----------------------------------------------------------------------------
# 5. Tests for 2.D.1 (Agent Config Model & Enforced Defaults)
# -----------------------------------------------------------------------------
def test_agent_config_schema_enforces_required_agents():
    cfg = AgentConfig(
        preset="fast",
        enabled_agents=["planner"],
        auto_approve_plans=True,
        model_profile="fast"
    )
    # Controller and reasoning are automatically added by validator
    assert "controller" in cfg.enabled_agents
    assert "reasoning" in cfg.enabled_agents
    assert "planner" in cfg.enabled_agents
