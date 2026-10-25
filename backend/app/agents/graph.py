"""
NEXUS LangGraph Cognitive Loop: Complete Assembly
Milestone 4 — Full Cognitive Loop with Tool Execution, Human Approval Checkpoint,
Evaluation Agent, and Bounded Auto-Replan Loop
"""

import logging
from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.agents.state import CogState
from app.agents.understanding import understanding_node
from app.agents.controller import controller_node
from app.agents.memory_agent import memory_recall_node, memory_propose_node
from app.agents.learning_agent import learning_hints_node
from app.services.learning import learning_service
from app.db.session import async_session_maker
from app.db.models import Run
from app.agents.planner import plan_generate_node, plan_wait_node
from app.agents.retrieval_agent import retrieval_agent_node
from app.agents.execute import (
    tool_decide_node,
    tool_propose_node,
    tool_wait_node,
    tool_run_node,
    should_check_tools,
    route_after_tool_run,
)
from app.agents.evaluator import evaluate_node, route_after_evaluation
from app.agents.reasoning import create_reasoning_node
from app.agents.registry import guarded, traced
from app.core.llm import LLMProvider, default_llm_provider, get_llm_provider

logger = logging.getLogger("nexus.agents.graph")


# ---------------------------------------------------------------------------
# Node Definitions
# ---------------------------------------------------------------------------

@traced("context_gather")
async def context_gather_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalls confirmed user memories and retrieves strategy hints and retrieval boosts.
    """
    enabled = state.get("enabled_agents", [])
    memories = []
    if "memory" in enabled:
        mem_res = await memory_recall_node(state)
        memories = mem_res.get("memories", [])

    strategy_hints = state.get("strategy_hints", [])
    retrieval_boosts = state.get("retrieval_boosts", {})
    if "learning" in enabled:
        learn_res = await learning_hints_node(state)
        strategy_hints = learn_res.get("strategy_hints", [])
        retrieval_boosts = learn_res.get("retrieval_boosts", {})

    return {
        "memories": memories,
        "strategy_hints": strategy_hints,
        "retrieval_boosts": retrieval_boosts,
    }


@traced("finalize")
async def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Finalizes response, extracts memory proposals, and commits learning signals."""
    enabled = state.get("enabled_agents", [])
    proposals = []
    if "memory" in enabled:
        prop_res = await memory_propose_node(state)
        proposals = prop_res.get("memory_proposals", [])

    # Record learning outcome if learning agent is enabled
    if "learning" in enabled and state.get("user_id") and state.get("run_id"):
        try:
            user_id = state.get("user_id", "")
            run_id = state.get("run_id", "")
            understanding = state.get("understanding") or {}
            intent = understanding.get("intent", "general") if isinstance(understanding, dict) else "general"

            plan = state.get("plan")
            plan_decision = state.get("plan_decision") or {}
            plan_unchanged = bool(plan and not plan_decision.get("edited_steps") and not plan_decision.get("replanned"))
            plan_edits_count = len(plan_decision.get("edited_steps", []))
            plan_replanned = bool(plan_decision.get("replanned", False))

            tool_calls = state.get("tool_calls", [])
            tools_success = None
            if tool_calls:
                tools_success = all(tc.get("status") == "done" for tc in tool_calls)

            eval_res = state.get("evaluation") or {}
            eval_score = eval_res.get("score") if isinstance(eval_res, dict) else None

            async with async_session_maker() as session:
                dummy_run = Run(id=run_id, user_id=user_id, conversation_id=state.get("conversation_id", ""))
                await learning_service.record_run_outcome(
                    db=session,
                    user_id=user_id,
                    run=dummy_run,
                    intent=intent,
                    plan_approved_unchanged=plan_unchanged,
                    plan_edits_count=plan_edits_count,
                    plan_replanned=plan_replanned,
                    tools_success=tools_success,
                    run_completed=True,
                    eval_score=eval_score,
                )
        except Exception as e:
            logger.warning(f"Failed to record learning signals in finalize: {e}")

    return {"memory_proposals": proposals}


# ---------------------------------------------------------------------------
# Routing Functions
# ---------------------------------------------------------------------------

def route_after_controller(state: Dict[str, Any]) -> str:
    tier = state.get("tier", "simple")
    if tier == "simple":
        if should_check_tools(state):
            return "tool_decide"
        return "reason"
    return "context_gather"


def route_after_context_gather(state: Dict[str, Any]) -> str:
    tier = state.get("tier", "simple")
    enabled = state.get("enabled_agents", [])
    if tier == "complex" and "planner" in enabled:
        return "plan_generate"
    if "retrieval" in enabled:
        return "retrieval"
    if should_check_tools(state):
        return "tool_decide"
    return "reason"


def route_after_plan_approval(state: Dict[str, Any]) -> str:
    decision = state.get("plan_decision", {})
    action = decision.get("action", "approve")
    replans = state.get("replans", 0)
    enabled = state.get("enabled_agents", [])

    if action == "replan" and replans < 3:
        return "plan_generate"

    if "retrieval" in enabled:
        return "retrieval"
    if should_check_tools(state):
        return "tool_decide"
    return "reason"


def route_after_retrieval(state: Dict[str, Any]) -> str:
    if should_check_tools(state):
        return "tool_decide"
    return "reason"


def route_after_tool_decide_branch(state: Dict[str, Any]) -> str:
    if state.get("pending_tool_call"):
        return "tool_propose"
    return "reason"


def route_after_reason_node(state: Dict[str, Any]) -> str:
    enabled = state.get("enabled_agents", [])
    tier = state.get("tier", "simple")
    # In Tier 1 without evaluation agent, finalize directly
    if "evaluation" in enabled or tier in ("document", "complex"):
        return "evaluate"
    return "finalize"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_graph(
    checkpointer: Optional[BaseCheckpointSaver] = None,
    llm: Optional[LLMProvider] = None,
):
    """
    Builds the full NEXUS cognitive loop with checkpointer and conditional branches.
    """
    llm_provider = llm or default_llm_provider
    builder = StateGraph(CogState)

    # Add All Nodes
    builder.add_node("understanding", understanding_node)
    builder.add_node("controller", controller_node)
    builder.add_node("context_gather", context_gather_node)
    builder.add_node("plan_generate", plan_generate_node)
    builder.add_node("plan_wait", plan_wait_node)
    builder.add_node("retrieval", retrieval_agent_node)
    builder.add_node("tool_decide", tool_decide_node)
    builder.add_node("tool_propose", tool_propose_node)
    builder.add_node("tool_wait", tool_wait_node)
    builder.add_node("tool_run", tool_run_node)
    builder.add_node("reason", create_reasoning_node(llm_provider))
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("finalize", finalize_node)

    # Primary Edges
    builder.add_edge(START, "understanding")
    builder.add_edge("understanding", "controller")

    # Branch after Controller
    builder.add_conditional_edges(
        "controller",
        route_after_controller,
        {
            "tool_decide": "tool_decide",
            "reason": "reason",
            "context_gather": "context_gather",
        },
    )

    # Branch after Context Gather
    builder.add_conditional_edges(
        "context_gather",
        route_after_context_gather,
        {
            "plan_generate": "plan_generate",
            "retrieval": "retrieval",
            "tool_decide": "tool_decide",
            "reason": "reason",
        },
    )

    # Planner loop
    builder.add_edge("plan_generate", "plan_wait")
    builder.add_conditional_edges(
        "plan_wait",
        route_after_plan_approval,
        {
            "plan_generate": "plan_generate",
            "retrieval": "retrieval",
            "tool_decide": "tool_decide",
            "reason": "reason",
        },
    )

    # Retrieval to Tool Decide or Reason
    builder.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {
            "tool_decide": "tool_decide",
            "reason": "reason",
        },
    )

    # Tool Execution Sub-loop
    builder.add_conditional_edges(
        "tool_decide",
        route_after_tool_decide_branch,
        {
            "tool_propose": "tool_propose",
            "reason": "reason",
        },
    )
    builder.add_edge("tool_propose", "tool_wait")
    builder.add_edge("tool_wait", "tool_run")
    builder.add_conditional_edges(
        "tool_run",
        route_after_tool_run,
        {
            "tool_decide": "tool_decide",
            "reason": "reason",
        },
    )

    # Reason to Evaluate or Finalize
    builder.add_conditional_edges(
        "reason",
        route_after_reason_node,
        {
            "evaluate": "evaluate",
            "finalize": "finalize",
        },
    )

    # Evaluate loop (retry to plan_generate/reason or finalize)
    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {
            "plan_generate": "plan_generate",
            "reason": "reason",
            "finalize": "finalize",
        },
    )

    # Finalize to END
    builder.add_edge("finalize", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()
