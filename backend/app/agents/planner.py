"""
NEXUS Planner Agent and Human-in-the-Loop Checkpoint
Step 2.B.3 — Structured plan generation, topological validation, and pause/resume checkpoint
"""

from collections import defaultdict, deque
import logging
from typing import Any, Dict, List, Optional

from langgraph.types import interrupt, Command

from app.agents.registry import guarded, traced
from app.core.llm import get_llm_provider
from app.schemas.plan import Plan, PlanStep, PlanDecision

logger = logging.getLogger("nexus.agents.planner")


def validate_and_toposort_steps(steps: List[PlanStep]) -> List[PlanStep]:
    """
    Validates that:
    1. depends_on references exist in the step set.
    2. Dependency graph is acyclic.
    3. Returns steps topologically sorted.
    Raises ValueError on invalid references or cycle.
    """
    step_map = {s.id: s for s in steps}
    in_degree = {s.id: 0 for s in steps}
    adj = defaultdict(list)

    for s in steps:
        for dep in s.depends_on:
            if dep not in step_map:
                raise ValueError(f"Step '{s.id}' references non-existent prerequisite '{dep}'")
            adj[dep].append(s.id)
            in_degree[s.id] += 1

    # Kahn's algorithm
    queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
    sorted_steps: List[PlanStep] = []

    while queue:
        curr_id = queue.popleft()
        sorted_steps.append(step_map[curr_id])
        for neighbor in adj[curr_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_steps) != len(steps):
        raise ValueError("Cyclic dependency detected in proposed plan steps")

    return sorted_steps


@guarded("planner")
@traced("plan_generate")
async def plan_generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a structured execution plan (3-7 steps) using LLMProvider.structured.
    Takes into account Understanding, user context, memories, strategy hints, and any replan feedback.
    """
    user_input = state.get("user_input", "")
    understanding = state.get("understanding", {})
    memories = state.get("memories", [])
    hints = state.get("strategy_hints", [])
    plan_decision = state.get("plan_decision", {})
    previous_plan = state.get("plan", {})
    profile = state.get("profile", "fast")

    feedback = plan_decision.get("feedback") if plan_decision else None

    # Construct prompt
    prompt = f"""You are the NEXUS Planner Agent.
Break down the user's objective into an actionable, acyclic 3 to 7 step execution plan.

Goal / Request: {user_input}
Understanding Intent: {understanding.get('intent')}
Domain: {understanding.get('domain')}
Requirements: {understanding.get('requirements', [])}
Recalled Context / Memories: {memories}
Strategy Hints: {hints}
"""
    if feedback and previous_plan:
        prompt += f"""
PREVIOUS PLAN:
{previous_plan}

USER REPLAN FEEDBACK:
"{feedback}"
Please adapt the plan specifically to address this feedback.
"""

    prompt += "\nOutput strictly a valid JSON matching the Plan schema with 'goal' and 3 to 7 'steps'."

    try:
        llm = get_llm_provider()
        plan_obj: Plan = await llm.structured(
            Plan,
            prompt=prompt,
            system="You are an expert system planner. Produce concise, logically ordered plans.",
            profile=profile
        )

        # Topological sorting and validation
        sorted_steps = validate_and_toposort_steps(plan_obj.steps)
        plan_dict = {
            "goal": plan_obj.goal,
            "steps": [s.model_dump() for s in sorted_steps]
        }
        return {"plan": plan_dict}

    except Exception as exc:
        logger.warning(f"Planner LLM generation or validation failed: {exc}. Producing safe fallback plan.")
        requirements = understanding.get("requirements", [])
        if not requirements:
            requirements = ["Analyze requirements", "Synthesize response"]

        fallback_steps = [
            PlanStep(
                id=f"step_{idx+1}",
                title=f"Execute {req}",
                detail=f"Focus on {req} according to user specifications",
                depends_on=[f"step_{idx}"] if idx > 0 else [],
                needs_retrieval=True
            ).model_dump()
            for idx, req in enumerate(requirements[:5])
        ]

        return {
            "plan": {
                "goal": user_input[:80],
                "steps": fallback_steps
            }
        }


def plan_wait_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Human-in-the-Loop plan approval checkpoint.
    
    IMPORTANT ARCHITECTURAL NOTE:
    NO LLM call must exist in this node!
    When a LangGraph run resumes after interrupt(), this node re-executes from the top.
    Having LLM calls here would waste GPU compute, duplicate tokens, and trigger unexpected state mutations.
    """
    auto_approve = state.get("auto_approve_plans", False) or (state.get("retries", 0) > 0)
    if auto_approve:
        logger.info("Auto-approve plans is enabled. Bypassing interrupt.")
        return {
            "plan_decision": {
                "action": "approve",
                "auto_approve_future": True
            }
        }

    plan = state.get("plan", {})
    run_id = state.get("run_id", "")

    # Pause execution and await client decision
    decision_data = interrupt({
        "type": "plan_proposed",
        "run_id": run_id,
        "plan": plan,
        "requires_approval": True
    })

    # When resumed via Command(resume=decision_data), decision_data is received here
    if isinstance(decision_data, dict):
        return {"plan_decision": decision_data}
    elif isinstance(decision_data, PlanDecision):
        return {"plan_decision": decision_data.model_dump()}
    else:
        return {"plan_decision": {"action": "approve"}}


def route_after_plan_wait(state: Dict[str, Any]) -> str:
    """
    Routing logic following the user's plan decision.
    - replan: loop back to plan_generate (max 3 replans)
    - edit: update plan with edited steps and continue to retrieval
    - approve: continue to retrieval
    """
    decision = state.get("plan_decision", {})
    action = decision.get("action", "approve")
    replans = state.get("replans", 0)

    if action == "replan":
        if replans >= 3:
            logger.warning("Max replans (3) reached. Forcing approval to prevent infinite loop.")
            return "retrieval"
        return "plan_generate"

    return "retrieval"


def apply_plan_decision_mutations(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to apply user edits or update auto_approve settings in state.
    """
    decision = state.get("plan_decision", {})
    action = decision.get("action", "approve")
    updates: Dict[str, Any] = {}

    if decision.get("auto_approve_future"):
        updates["auto_approve_plans"] = True

    if action == "replan":
        updates["replans"] = state.get("replans", 0) + 1

    elif action == "edit" and "steps" in decision and decision["steps"]:
        try:
            steps_pydantic = [
                s if isinstance(s, PlanStep) else PlanStep(**s)
                for s in decision["steps"]
            ]
            sorted_steps = validate_and_toposort_steps(steps_pydantic)
            curr_plan = state.get("plan", {})
            curr_plan["steps"] = [s.model_dump() for s in sorted_steps]
            updates["plan"] = curr_plan
        except Exception as exc:
            logger.error(f"Failed to apply edited steps: {exc}")

    return updates
