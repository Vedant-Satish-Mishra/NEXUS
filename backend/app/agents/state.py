"""
NEXUS Cognitive State (CogState) Definition
Base TypedDict schema representing the cognitive loop state across LangGraph nodes.
"""

import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict


class CogState(TypedDict, total=False):
    # Core identifiers
    user_id: str
    conversation_id: str
    run_id: str

    # Input & conversation context
    user_input: str
    history: List[Dict[str, Any]]
    file_ids: List[str]

    # Configuration snapshot
    enabled_agents: List[str]
    profile: str
    auto_approve_plans: bool

    # Cognitive pipeline data
    understanding: Dict[str, Any]
    tier: str
    route: List[str]

    # Context & memory
    memories: List[Dict[str, Any]]
    strategy_hints: List[str]
    retrieval_boosts: Dict[str, float]

    # Planning
    plan: Dict[str, Any]
    plan_decision: Dict[str, Any]
    replans: int

    # Evidence & tools
    docs: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    pending_tool_call: Optional[Dict[str, Any]]
    tool_decision: Optional[Dict[str, Any]]
    tool_iterations: int

    # Reasoning output & evaluation
    answer: str
    evaluation: Dict[str, Any]
    retries: int
    critique: Optional[str]
    low_confidence: bool
    memory_proposals: List[Dict[str, Any]]

    # Trace reducer: concatenates execution traces
    trace: Annotated[List[Dict[str, Any]], operator.add]
