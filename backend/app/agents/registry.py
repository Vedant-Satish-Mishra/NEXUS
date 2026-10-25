"""
NEXUS Agent Registry and Enforcement Decorators
Step 2.B.1 — Full CogState, agent registry and permission guard.
"""

from dataclasses import dataclass
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("nexus.agents.registry")


@dataclass(frozen=True)
class AgentMeta:
    name: str
    label: str
    required: bool
    uses_llm: bool
    description: str


# System-wide Agent Definitions
AGENTS: Dict[str, AgentMeta] = {
    "controller": AgentMeta(
        name="controller",
        label="Executive Controller",
        required=True,
        uses_llm=False,
        description="Classifies intent and deterministically routes messages across tiers."
    ),
    "reasoning": AgentMeta(
        name="reasoning",
        label="Reasoning Agent",
        required=True,
        uses_llm=True,
        description="Generates final grounded synthesis, answers, and orchestrates tool calls."
    ),
    "planner": AgentMeta(
        name="planner",
        label="Planner Agent",
        required=False,
        uses_llm=True,
        description="Deconstructs complex goals into structured, acyclic execution plans for approval."
    ),
    "retrieval": AgentMeta(
        name="retrieval",
        label="Retrieval Agent",
        required=False,
        uses_llm=False,
        description="Generates targeted queries and searches hybrid knowledge base with strict tenant isolation."
    ),
    "memory": AgentMeta(
        name="memory",
        label="Memory Agent",
        required=False,
        uses_llm=False,
        description="Recalls past interactions, preferences, and proposes new confirmed memories."
    ),
    "evaluation": AgentMeta(
        name="evaluation",
        label="Evaluation Agent",
        required=False,
        uses_llm=True,
        description="Applies deterministic safety/rubric checks and optional self-correction loops."
    ),
    "learning": AgentMeta(
        name="learning",
        label="Learning System",
        required=False,
        uses_llm=False,
        description="Adapts retrieval ranking and strategy hints from human feedback signals."
    ),
}

# Standard presets
PRESETS = {
    "fast": ["reasoning"],
    "balanced": ["reasoning", "retrieval", "memory", "evaluation"],
    "full": ["reasoning", "retrieval", "planner", "memory", "evaluation", "learning"]
}


def guarded(agent_name: str):
    """
    Two-layer permission enforcement decorator.
    A disabled agent must never execute its logic.
    If disabled by the user, returns a skipped trace record immediately.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(state: Dict[str, Any], *args, **kwargs):
            enabled = state.get("enabled_agents", [])
            # Controller and reasoning are required and always treated as enabled
            if agent_name in ["controller", "reasoning"]:
                is_enabled = True
            else:
                is_enabled = agent_name in enabled

            if not is_enabled:
                logger.info(f"Guarded agent '{agent_name}' is disabled in state. Skipping execution.")
                return {
                    "trace": [{
                        "node": agent_name,
                        "status": "skipped",
                        "summary": f"Agent '{agent_name}' disabled by user",
                        "reason": "disabled by user",
                        "ms": 0
                    }]
                }
            return await func(state, *args, **kwargs)
        return wrapper
    return decorator


def traced(node_name: Optional[str] = None):
    """
    Execution tracing and fault isolation decorator.
    Records duration_ms, catches exceptions to prevent graph collapse,
    and appends a standardized trace event to state['trace'].
    """
    def decorator(func: Callable):
        name = node_name or func.__name__

        @functools.wraps(func)
        async def wrapper(state: Dict[str, Any], *args, **kwargs):
            t0 = time.perf_counter()
            try:
                result = await func(state, *args, **kwargs)
                ms = int((time.perf_counter() - t0) * 1000)
                
                # Merge or inject trace entry
                trace_entry = {
                    "node": name,
                    "status": "ok",
                    "ms": ms,
                    "summary": f"{name} executed successfully"
                }
                
                if isinstance(result, dict):
                    if "trace" in result and result["trace"]:
                        if result["trace"][-1].get("status") == "error":
                            return result
                        result["trace"].append(trace_entry)
                    else:
                        result["trace"] = [trace_entry]
                    return result
                return {"trace": [trace_entry]}

            except Exception as exc:
                ms = int((time.perf_counter() - t0) * 1000)
                logger.error(f"Error executing node '{name}': {exc}", exc_info=True)
                error_entry = {
                    "node": name,
                    "status": "error",
                    "ms": ms,
                    "summary": f"Execution error in {name}",
                    "error": str(exc)
                }
                # Safe failure: never crash the graph
                return {
                    "trace": [error_entry]
                }
        return wrapper
    return decorator
