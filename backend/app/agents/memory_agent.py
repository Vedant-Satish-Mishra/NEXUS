"""
NEXUS Memory Agent (Milestone 3)
Step 3.B.1 — Memory recall, rule-based proposals, and conversation compaction.
"""

import logging
from typing import Any, Dict, List

from app.agents.registry import guarded, traced
from app.db.session import async_session_maker
from app.schemas.core import Principal
from app.services.memory import MemoryService

logger = logging.getLogger("nexus.agents.memory")
memory_service = MemoryService(session_factory=async_session_maker)


def compact_history(history: List[Dict[str, str]], keep_last: int = 8) -> List[Dict[str, str]]:
    """
    Deterministic conversation history compaction without extra LLM call.
    Keeps last `keep_last` turns verbatim; summarizes older assistant messages
    to their first sentence.
    """
    if len(history) <= keep_last:
        return history

    older = history[:-keep_last]
    recent = history[-keep_last:]

    compacted_older = []
    for msg in older:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "assistant":
            parts = content.split(". ")
            first_sentence = parts[0].strip()
            if not first_sentence.endswith("."):
                first_sentence += "."
            compacted_older.append({"role": role, "content": f"[Summary: {first_sentence}]"})
        else:
            compacted_older.append(msg)

    return compacted_older + recent


@guarded("memory")
@traced("memory_recall")
async def memory_recall_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalls confirmed user memories relevant to the query.
    Ranked by similarity * (0.7 + 0.3 * importance) * recency_factor.
    """
    user_id = state.get("user_id", "default_user")
    user_input = state.get("user_input", "")
    principal = Principal(user_id=user_id)

    recalled = await memory_service.recall_memories(
        principal=principal,
        query=user_input,
        k=3
    )
    return {"memories": recalled}


@guarded("memory")
@traced("memory_propose")
async def memory_propose_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Proposes new memories based on user explicit statements and completed goals.
    Never persists without explicit user confirmation.
    """
    user_id = state.get("user_id", "default_user")
    run_id = state.get("run_id", "default_run")
    user_input = state.get("user_input", "")
    plan = state.get("plan")
    tier_name = state.get("tier", "simple")
    tier_num = 3 if tier_name == "complex" else (2 if tier_name == "document" else 1)

    proposals = await memory_service.extract_and_propose(
        user_id=user_id,
        run_id=run_id,
        user_input=user_input,
        plan=plan,
        tier=tier_num
    )
    return {"memory_proposals": proposals}
