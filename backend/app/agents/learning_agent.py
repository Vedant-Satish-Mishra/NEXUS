"""
NEXUS Learning Agent (Step 5.B.1)
Node for gathering learned strategy hints and retrieval source boosts,
and emitting outcome signals at run finalization.
"""
from typing import Any, Dict, List
from app.agents.registry import guarded, traced
from app.agents.state import CogState
from app.db.session import async_session_maker
from app.schemas.core import Principal
from app.services.learning import learning_service


@guarded("learning")
@traced("learning")
async def learning_hints_node(state: CogState) -> Dict[str, Any]:
    """
    Retrieves aggregated strategy hints and evidence source boosts for the user and intent.
    Respects agent enablement: if 'learning' is not enabled, returns empty hints/boosts.
    """
    user_id = state.get("user_id", "")
    if not user_id:
        return {"strategy_hints": [], "retrieval_boosts": {}}

    intent = "general"
    understanding = state.get("understanding") or {}
    if isinstance(understanding, dict):
        intent = understanding.get("intent", "general")

    principal = Principal(user_id=user_id, role="user")

    try:
        async with async_session_maker() as session:
            hints, boosts = await learning_service.get_hints_and_boosts(
                db=session,
                principal=principal,
                intent=intent,
            )
            return {
                "strategy_hints": hints,
                "retrieval_boosts": boosts,
            }
    except Exception:
        return {"strategy_hints": [], "retrieval_boosts": {}}
