"""
NEXUS Executive Controller
Step 2.B.2 — Deterministic tier classification and routing (Pure Code, No LLM)
"""

import logging
from typing import Any, Dict, List

from app.agents.registry import traced

logger = logging.getLogger("nexus.agents.controller")

COMPLEX_KEYWORDS = [
    "plan", "roadmap", "schedule", "compare", "comparison", "design",
    "step-by-step", "strategy", "prepare", "curriculum", "syllabus", "guide"
]

DOC_TRIGGERS = ["my notes", "document", "file", "uploaded", "pdf", "summarize", "notes"]


@traced("controller")
async def controller_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifies tier and generates execution route based on:
    1. Understanding complexity & message features (word count, files, triggers)
    2. Enabled agent permissions (clamping tier and emitting hints on downgrades)
    3. Deterministic DAG route construction
    """
    user_input = state.get("user_input", "")
    file_ids = state.get("file_ids", [])
    enabled_agents = state.get("enabled_agents", [])
    understanding = state.get("understanding", {})

    input_lower = user_input.lower()
    word_count = len(user_input.strip().split())

    # Step 1: Base Tier from Understanding complexity
    raw_complexity = understanding.get("complexity", "simple")
    if raw_complexity in ["simple", "document", "complex"]:
        calculated_tier = raw_complexity
    else:
        calculated_tier = "simple"

    # Apply hard rule adjustments:
    # Rule A: Files attached or document keywords -> at least "document"
    has_files = bool(file_ids and len(file_ids) > 0)
    has_doc_trigger = any(trigger in input_lower for trigger in DOC_TRIGGERS)
    if (has_files or has_doc_trigger) and calculated_tier == "simple":
        calculated_tier = "document"

    # Rule B: Complex keywords or >= 30 words -> "complex"
    has_complex_keyword = any(kw in input_lower for kw in COMPLEX_KEYWORDS)
    if (has_complex_keyword or word_count >= 30):
        calculated_tier = "complex"

    # Step 2: Permission Clamping & Hint Generation
    hints: List[Dict[str, str]] = []
    final_tier = calculated_tier

    if final_tier == "complex":
        if "planner" not in enabled_agents:
            hints.append({
                "agent": "planner",
                "reason": "Enable Planner for multi-step breakdown, editable milestones, and plan approval."
            })
            if "retrieval" in enabled_agents:
                final_tier = "document"
            else:
                final_tier = "simple"

    if final_tier == "document":
        if "retrieval" not in enabled_agents:
            hints.append({
                "agent": "retrieval",
                "reason": "Enable Retrieval to ground answers with citations from your uploaded notes and knowledge base."
            })
            final_tier = "simple"

    # Step 3: Compute deterministic Route
    route: List[str] = []
    if final_tier == "simple":
        route = ["reason"]
    elif final_tier == "document":
        route = ["context_gather"]
        if "retrieval" in enabled_agents:
            route.append("retrieval")
        route.append("reason")
    elif final_tier == "complex":
        route = ["context_gather"]
        if "planner" in enabled_agents:
            route.extend(["plan_generate", "plan_wait"])
        if "retrieval" in enabled_agents:
            route.append("retrieval")
        route.append("reason")

    logger.info(
        f"Executive Controller: input='{user_input[:40]}...' -> raw={calculated_tier}, "
        f"final={final_tier}, route={route}, hints={hints}"
    )

    return {
        "tier": final_tier,
        "route": route,
        "agent_hints": hints
    }
