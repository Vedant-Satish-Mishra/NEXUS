"""
NEXUS Understanding Agent
Step 2.B.2 — Structured intent and requirement extraction
"""

import logging
import re
from typing import Any, Dict

from app.agents.registry import guarded, traced
from app.core.llm import get_llm_provider
from app.schemas.understanding import Understanding

logger = logging.getLogger("nexus.agents.understanding")

COMPLEX_KEYWORDS = [
    "plan", "roadmap", "schedule", "compare", "comparison", "design",
    "step-by-step", "strategy", "prepare", "curriculum", "syllabus", "guide"
]

SEMINAR_EXAMPLE = """Example:
User: "I am a 4th-year IT student preparing for Java placements in 4 months. Give me a study roadmap."
JSON:
{
  "intent": "placement_preparation",
  "domain": "Java",
  "user_context": {"year": "4th-year", "branch": "IT", "time_available": "4 months"},
  "requirements": ["Core Java", "DSA", "DBMS", "Interview Preparation"],
  "output_type": "4-month preparation plan",
  "complexity": "complex",
  "needs_retrieval": true,
  "needs_plan": true,
  "tools_required": [],
  "constraints": ["4 months duration"],
  "privacy_mode": "local_only"
}"""


def is_non_trivial(user_input: str, file_ids: list[str]) -> bool:
    """Checks whether the user message is non-trivial enough to warrant LLM Understanding."""
    if file_ids and len(file_ids) > 0:
        return True
    
    words = user_input.strip().split()
    if len(words) >= 8:
        return True
        
    lower = user_input.lower()
    for kw in COMPLEX_KEYWORDS:
        if kw in lower:
            return True
            
    doc_triggers = ["my notes", "document", "file", "uploaded", "pdf", "summarize"]
    for dt in doc_triggers:
        if dt in lower:
            return True

    return False


@traced("understanding")
async def understanding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structured Understanding extraction node.
    Skips LLM call if message is trivial or both retrieval & planner are disabled.
    """
    user_input = state.get("user_input", "")
    file_ids = state.get("file_ids", [])
    enabled_agents = state.get("enabled_agents", [])
    profile = state.get("profile", "fast")

    # Guard: only run LLM if planner or retrieval is enabled AND message is non-trivial
    needs_understanding = (
        ("retrieval" in enabled_agents or "planner" in enabled_agents)
        and is_non_trivial(user_input, file_ids)
    )

    if not needs_understanding:
        # Default lightweight fallback without LLM overhead
        default_understanding = Understanding(
            intent="general_query",
            domain=None,
            user_context={},
            requirements=[],
            output_type="answer",
            complexity="simple",
            needs_retrieval=bool(file_ids),
            needs_plan=False,
            tools_required=[],
            constraints=[],
            privacy_mode="local_only"
        )
        return {"understanding": default_understanding.model_dump()}

    prompt = f"""You are the NEXUS Understanding Agent.
Analyze the user message and extract structured intent, domain, user context, decomposed requirements, output type, and complexity.

{SEMINAR_EXAMPLE}

User Message: "{user_input}"
Attached File IDs: {file_ids}

Respond strictly with a valid JSON object matching the schema."""

    try:
        llm = get_llm_provider()
        extracted: Understanding = await llm.structured(
            Understanding,
            prompt=prompt,
            system="You extract structured query analysis in JSON format.",
            profile=profile
        )
        return {"understanding": extracted.model_dump()}
    except Exception as exc:
        logger.warning(f"Understanding structured extraction failed: {exc}. Using heuristic fallback.")
        # Safe fallback: never fail the pipeline
        fallback = Understanding(
            intent="general_query",
            domain=None,
            user_context={},
            requirements=[user_input[:80]] if len(user_input) > 20 else [],
            output_type="answer",
            complexity="complex" if any(k in user_input.lower() for k in COMPLEX_KEYWORDS) else "simple",
            needs_retrieval=bool(file_ids),
            needs_plan=False
        )
        return {"understanding": fallback.model_dump()}
