"""
NEXUS Retrieval Agent
Step 2.C.2 — Requirement-driven query extraction and vector retrieval (No LLM)
"""

import logging
from typing import Any, Dict, List

from app.agents.registry import guarded, traced
from app.rag.hybrid import HybridRetriever
from app.schemas.core import Principal

logger = logging.getLogger("nexus.agents.retrieval")
hybrid_retriever = HybridRetriever()


def extract_retrieval_queries(state: Dict[str, Any]) -> List[str]:
    """
    Builds focused queries from:
    1. Approved plan steps marked with needs_retrieval (if present)
    2. Understanding.requirements
    3. Fallback to raw user input
    Prefixed with domain when available.
    """
    domain = state.get("understanding", {}).get("domain")
    prefix = f"{domain}: " if domain else ""
    queries: List[str] = []

    # Priority 1: Plan steps
    plan = state.get("plan", {})
    steps = plan.get("steps", [])
    if steps:
        for s in steps:
            if s.get("needs_retrieval", True):
                title = s.get("title", "")
                detail = s.get("detail", "")
                query_text = f"{prefix}{title} {detail}".strip()
                if query_text:
                    queries.append(query_text)

    # Priority 2: Understanding requirements
    if not queries:
        requirements = state.get("understanding", {}).get("requirements", [])
        for req in requirements:
            q = f"{prefix}{req}".strip()
            if q:
                queries.append(q)

    # Priority 3: Raw user input fallback
    if not queries:
        raw_msg = state.get("user_input", "").strip()
        if raw_msg:
            queries.append(f"{prefix}{raw_msg}".strip())

    return queries[:5]


@guarded("retrieval")
@traced("retrieval")
async def retrieval_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieval Agent: pure deterministic orchestration.
    Generates targeted queries, calls RetrievalService, and returns retrieved chunks.
    """
    queries = extract_retrieval_queries(state)
    user_id = state.get("user_id", "default_user")
    conversation_id = state.get("conversation_id", "default_conv")
    principal = Principal(user_id=user_id, conversation_id=conversation_id)

    docs_map: Dict[str, Dict[str, Any]] = {}
    source_boosts = state.get("retrieval_boosts")
    for q in queries:
        chunk_results = await hybrid_retriever.search_hybrid(
            principal=principal,
            query=q,
            top_k=4,
            min_score=0.35,
            source_boosts=source_boosts,
        )
        for c in chunk_results:
            cid = c["id"]
            if cid not in docs_map or c["score"] > docs_map[cid]["score"]:
                docs_map[cid] = c

    merged_docs = list(docs_map.values())
    merged_docs.sort(key=lambda x: x["score"], reverse=True)
    final_docs = merged_docs[:6]

    logger.info(f"Retrieval Agent: generated {len(queries)} queries, found {len(final_docs)} hybrid chunks.")
    return {"docs": final_docs}
