"""
NEXUS SSE Event Stream Adapter (Milestone 2)
Step 2.B.5 — Adapts full LangGraph multi-agent loop into strongly-typed SSE event stream
"""

import logging
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from app.agents.state import CogState
from app.schemas.events import (
    AgentHintEvent,
    CitationItem,
    ErrorEvent,
    FinalEvent,
    MemoryProposalEvent,
    NodeFinishedEvent,
    NodeStartedEvent,
    PlanProposedEvent,
    RunStartedEvent,
    SourcesEvent,
    TokenEvent,
    UnderstandingEvent,
    SSEEvent,
)
from app.schemas.run import MemoryProposal
from app.schemas.plan import Plan
from app.schemas.understanding import Understanding

logger = logging.getLogger("nexus.agents.events")


async def stream_graph_events(
    graph,
    initial_state: CogState,
    thread_id: str,
    run_id: str,
    tier: int = 1,
    enabled_agents: Optional[List[str]] = None,
    message_id: Optional[str] = None,
) -> AsyncIterator[SSEEvent]:
    """
    Executes compiled StateGraph and yields formatted SSE events:
    run_started -> node_started/node_finished (for each agent) -> understanding ->
    agent_hint* -> plan_proposed -> sources -> token* -> final
    """
    actual_agents = enabled_agents or initial_state.get("enabled_agents") or ["controller", "reasoning"]
    actual_msg_id = message_id or str(uuid.uuid4())

    # 1. Emit RunStarted
    yield RunStartedEvent(
        run_id=run_id,
        tier=tier,
        enabled_agents=actual_agents,
    )

    # 2. Emit initial NodeStarted
    yield NodeStartedEvent(node="reason")

    config = {"configurable": {"thread_id": thread_id}}
    full_answer = ""
    citations: List[CitationItem] = []
    current_tier_int = tier

    try:
        async for mode, chunk in graph.astream(
            initial_state,
            config=config,
            stream_mode=["updates", "custom"],
        ):
            # Custom chunks (live tokens, direct sources)
            if mode == "custom":
                if isinstance(chunk, dict):
                    ctype = chunk.get("type")
                    if ctype == "token":
                        content = chunk.get("content", "")
                        full_answer += content
                        yield TokenEvent(content=content)
                    elif ctype == "sources":
                        src_items = [
                            CitationItem(
                                file=s.get("file", ""),
                                page=s.get("page", 1),
                                score=s.get("score", 0.0),
                                chunk_id=s.get("chunk_id", ""),
                                snippet=s.get("snippet")
                            )
                            for s in chunk.get("sources", [])
                        ]
                        citations = src_items
                        yield SourcesEvent(sources=src_items)
                    elif ctype == "plan_proposed":
                        plan_data = chunk.get("plan", {})
                        if plan_data:
                            yield PlanProposedEvent(
                                run_id=run_id,
                                plan=Plan(**plan_data),
                                requires_approval=chunk.get("requires_approval", True)
                            )
                elif isinstance(chunk, str):
                    full_answer += chunk
                    yield TokenEvent(content=chunk)

            # Node updates
            elif mode == "updates":
                if isinstance(chunk, dict):
                    # Check for LangGraph interrupt
                    if "__interrupt__" in chunk:
                        interrupt_val = chunk["__interrupt__"]
                        if isinstance(interrupt_val, tuple) and len(interrupt_val) > 0:
                            payload = interrupt_val[0].value if hasattr(interrupt_val[0], "value") else interrupt_val[0]
                        else:
                            payload = interrupt_val

                        if isinstance(payload, dict) and payload.get("type") == "plan_proposed":
                            plan_data = payload.get("plan", {})
                            yield PlanProposedEvent(
                                run_id=run_id,
                                plan=Plan(**plan_data),
                                requires_approval=True
                            )
                        # We pause stream here; wait for resume
                        return

                    for node_name, node_out in chunk.items():
                        if not isinstance(node_out, dict):
                            continue

                        # Extract node trace
                        traces = node_out.get("trace", [])
                        ms = 0
                        status = "ok"
                        summary = f"{node_name} completed"
                        if traces:
                            last_trace = traces[-1]
                            ms = last_trace.get("ms", 0)
                            status = last_trace.get("status", "ok")
                            summary = last_trace.get("summary", summary)

                        # Emit node finished
                        yield NodeFinishedEvent(
                            node=node_name,
                            summary=summary,
                            ms=ms,
                            status=status
                        )

                        # Specific Node Events
                        if node_name == "understanding" and "understanding" in node_out:
                            u_data = node_out["understanding"]
                            try:
                                yield UnderstandingEvent(understanding=Understanding(**u_data))
                            except Exception as e:
                                logger.warning(f"Could not construct UnderstandingEvent: {e}")

                        elif node_name == "controller":
                            hints = node_out.get("agent_hints", [])
                            for h in hints:
                                yield AgentHintEvent(agent=h["agent"], reason=h["reason"])

                        elif node_name == "plan_generate" and "plan" in node_out:
                            p_data = node_out["plan"]
                            try:
                                yield PlanProposedEvent(
                                    run_id=run_id,
                                    plan=Plan(**p_data),
                                    requires_approval=True
                                )
                            except Exception as e:
                                logger.warning(f"Could not construct PlanProposedEvent: {e}")

                        elif node_name == "retrieval" and "docs" in node_out:
                            docs = node_out["docs"]
                            src_items = [
                                CitationItem(
                                    file=d.get("source", "knowledge_base"),
                                    page=d.get("page", 1),
                                    score=d.get("score", 0.0),
                                    chunk_id=d.get("id", ""),
                                    snippet=d.get("text", "")[:160]
                                )
                                for d in docs
                            ]
                            citations = src_items
                            yield SourcesEvent(sources=src_items)

                        elif node_name == "reason":
                            if "answer" in node_out and not full_answer:
                                full_answer = node_out["answer"]
                            if "citations" in node_out and not citations:
                                citations = [
                                    CitationItem(**c) for c in node_out["citations"]
                                ]

                        elif node_name == "finalize" and "memory_proposals" in node_out:
                            raw_props = node_out["memory_proposals"]
                            if raw_props:
                                try:
                                    yield MemoryProposalEvent(
                                        proposals=[
                                            MemoryProposal(
                                                id=p["id"],
                                                kind=p.get("kind", "long_term"),
                                                content=p["content"],
                                                status="pending"
                                            )
                                            for p in raw_props
                                        ]
                                    )
                                except Exception as e:
                                    logger.warning(f"Could not construct MemoryProposalEvent: {e}")

        # 4. Emit Final event
        yield FinalEvent(
            message_id=actual_msg_id,
            content=full_answer,
            citations=citations,
        )

    except Exception as exc:
        logger.error(f"Error in stream_graph_events: {exc}", exc_info=True)
        yield ErrorEvent(
            code="graph_execution_failed",
            message=f"Agent execution encountered an error: {str(exc)}",
        )
