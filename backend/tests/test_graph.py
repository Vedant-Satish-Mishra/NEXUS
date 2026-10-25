"""
Tests for Step 2.B.5:
NEXUS Cognitive Pipeline: LangGraph Runtime, Checkpointer, and Event Streaming
"""

import pytest
import pytest_asyncio
from typing import AsyncIterator, List, Dict, Any, Type
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import CogState
from app.agents.graph import build_graph
from app.agents.events import stream_graph_events
from app.schemas.events import (
    RunStartedEvent,
    NodeFinishedEvent,
    TokenEvent,
    FinalEvent,
    ErrorEvent,
)


class FakeStreamingLLM:
    """Fake LLM Provider for deterministic streaming tests."""
    def __init__(self, token_chunks: List[str]):
        self.chunks = token_chunks
        self.call_count = 0

    async def chat(self, messages: List[Dict[str, str]], **opts) -> str:
        self.call_count += 1
        return "".join(self.chunks)

    async def stream(self, messages: List[Dict[str, str]], **opts) -> AsyncIterator[str]:
        self.call_count += 1
        for chunk in self.chunks:
            yield chunk

    async def structured(self, model: Type[BaseModel], **opts) -> BaseModel:
        # Return default instance of requested model
        if hasattr(model, "__fields__") or hasattr(model, "model_fields"):
            return model.model_construct()
        return model()

    async def aclose(self) -> None:
        pass


@pytest.mark.asyncio
async def test_minimal_graph_execution_and_checkpointer():
    """Verify graph runs, streams tokens, writes to answer, and saves state to checkpointer."""
    checkpointer = MemorySaver()
    fake_llm = FakeStreamingLLM(["Hello", " ", "NEXUS", "!"])
    graph = build_graph(checkpointer=checkpointer, llm=fake_llm)

    run_id = "test-run-101"
    initial_state: CogState = {
        "user_id": "usr-1",
        "conversation_id": "conv-1",
        "run_id": run_id,
        "user_input": "Say hello to NEXUS",
        "history": [],
        "enabled_agents": ["controller", "reasoning"],
        "profile": "fast",
        "trace": [],
    }

    # Execute streaming
    events = []
    async for evt in stream_graph_events(
        graph=graph,
        initial_state=initial_state,
        thread_id=run_id,
        run_id=run_id,
        tier=1,
    ):
        events.append(evt)

    # 1. Assert event order
    assert len(events) >= 4
    assert isinstance(events[0], RunStartedEvent)
    assert events[0].run_id == run_id
    assert events[0].tier == 1

    token_events = [e for e in events if isinstance(e, TokenEvent)]
    assert len(token_events) == 4
    assert "".join([e.content for e in token_events]) == "Hello NEXUS!"

    node_finished_events = [e for e in events if isinstance(e, NodeFinishedEvent)]
    node_names = [e.node for e in node_finished_events]
    assert "understanding" in node_names
    assert "controller" in node_names
    assert "reason" in node_names

    final_events = [e for e in events if isinstance(e, FinalEvent)]
    assert len(final_events) == 1
    assert final_events[0].content == "Hello NEXUS!"

    # 2. Check checkpointer saved state with thread_id = run_id
    saved = checkpointer.get(config={"configurable": {"thread_id": run_id}})
    assert saved is not None
    saved_state = saved["channel_values"]
    assert saved_state["answer"] == "Hello NEXUS!"
    assert any(t["node"] == "reason" for t in saved_state["trace"])


@pytest.mark.asyncio
async def test_graph_error_handling():
    """Verify exceptions during generation produce graceful ErrorEvent without crash."""
    class FailingLLM:
        async def stream(self, messages, **opts):
            yield "Starting..."
            raise RuntimeError("GPU connection lost")

        async def chat(self, messages, **opts):
            raise RuntimeError("GPU connection lost")

        async def structured(self, model, **opts):
            return model.model_construct()

        async def aclose(self):
            pass

    graph = build_graph(checkpointer=MemorySaver(), llm=FailingLLM())
    initial_state: CogState = {
        "user_id": "usr-1",
        "conversation_id": "conv-1",
        "run_id": "err-run",
        "user_input": "Trigger failure",
        "enabled_agents": ["controller", "reasoning"],
        "trace": [],
    }

    events = []
    async for evt in stream_graph_events(
        graph=graph,
        initial_state=initial_state,
        thread_id="err-run",
        run_id="err-run",
    ):
        events.append(evt)

    # Nodes execute safely; reason encounters error but pipeline finishes gracefully
    node_fin = [e for e in events if isinstance(e, NodeFinishedEvent)]
    reason_fin = [e for e in node_fin if e.node == "reason"]
    assert len(reason_fin) == 1
    assert reason_fin[0].status == "error"
