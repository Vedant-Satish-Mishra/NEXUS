"""
NEXUS Runs Service
Manages run initiation, active concurrency locks, interrupts, resume queues,
and SSE event streaming with checkpoint persistence.
"""

import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator, Dict, Optional, Set
from fastapi import HTTPException, Request, status
from langgraph.types import Command
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.checkpointer import get_checkpointer
from app.agents.events import stream_graph_events
from app.agents.graph import build_graph
from app.agents.state import CogState
from app.core.llm import gpu_semaphore as gpu_worker_semaphore
from app.db.models import ChatAgentConfig, Message, Run, RunEvent, User
from app.schemas.events import SSEEvent
from app.schemas.plan import PlanDecision
from app.schemas.run import RunCreate

logger = logging.getLogger("nexus.services.runs")

# In-memory tracking of active runs per user (enforces 1 active run per user)
_active_user_runs: Dict[str, str] = {}
_active_runs_lock = asyncio.Lock()

# Resume queues for interrupted runs awaiting human decision
_resume_queues: Dict[str, asyncio.Queue] = {}


class ToolDecision(BaseModel):
    action: str = Field(..., description="Action: 'approve', 'edit', or 'deny'")
    code: Optional[str] = Field(None, description="Optional edited code or input")
    input: Optional[str] = Field(None, description="Optional edited input")


async def register_active_run(user_id: str, run_id: str) -> bool:
    """Registers an active run. Returns False if user already has an active run."""
    async with _active_runs_lock:
        if user_id in _active_user_runs:
            return False
        _active_user_runs[user_id] = run_id
        return True


async def unregister_active_run(user_id: str, run_id: str) -> None:
    """Unregisters an active run when finished, cancelled, or failed."""
    async with _active_runs_lock:
        if _active_user_runs.get(user_id) == run_id:
            del _active_user_runs[user_id]


class RunsService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_run(self, payload: RunCreate, current_user: User) -> Run:
        """
        Creates a new reasoning run:
        - Checks active run concurrency guard (409 Conflict if active run exists)
        - Saves user message BEFORE generation begins
        - Auto-titles conversation from first prompt (max 60 chars)
        """
        async with self.session_factory() as db:
            # Check conversation ownership
            from app.db.models import Conversation
            stmt = select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == current_user.id
            )
            res = await db.execute(stmt)
            conv = res.scalar_one_or_none()
            if not conv:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

            # Check active run guard
            can_start = await register_active_run(current_user.id, "pending")
            if not can_start:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another run is currently active for this user. Wait for it to finish.",
                )

            try:
                # Save user message before generation starts
                user_msg = Message(
                    conversation_id=conv.id,
                    role="user",
                    content=payload.message,
                    meta={"file_ids": payload.file_ids} if payload.file_ids else None
                )
                db.add(user_msg)

                # Auto-title conversation if default or empty
                if conv.title.strip().lower() in ("new chat", "untitled", ""):
                    clean_title = payload.message.strip().replace("\n", " ")[:60]
                    if clean_title:
                        conv.title = clean_title

                # Create Run record
                run = Run(
                    conversation_id=conv.id,
                    user_id=current_user.id,
                    status="queued",
                    tier=1,
                )
                db.add(run)
                await db.commit()
                await db.refresh(run)

                # Update active run tracker with real ID
                async with _active_runs_lock:
                    _active_user_runs[current_user.id] = run.id

                return run
            except Exception:
                await unregister_active_run(current_user.id, "pending")
                raise

    async def decide_plan(self, run_id: str, decision: PlanDecision, current_user: User) -> Dict[str, Any]:
        """
        Human-in-the-loop plan decision: approve, edit, or replan.
        Validates run ownership and awaiting_plan_approval status (409 otherwise).
        """
        async with self.session_factory() as db:
            stmt = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            if not run:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

            if run.status != "awaiting_plan_approval":
                if run.status in ("running", "completed"):
                    return {"status": "already_processed", "run_id": run_id}
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Run is not awaiting plan approval (current status: '{run.status}')"
                )

            # If auto_approve_future requested, persist to ChatAgentConfig
            if decision.auto_approve_future:
                cfg_stmt = select(ChatAgentConfig).where(ChatAgentConfig.conversation_id == run.conversation_id)
                cfg = (await db.execute(cfg_stmt)).scalar_one_or_none()
                if cfg:
                    cfg.auto_approve_plans = True
                    await db.commit()

            # Pass decision to waiting queue if active
            if run_id in _resume_queues:
                await _resume_queues[run_id].put(decision)

            return {"status": "decision_accepted", "run_id": run_id}

    async def decide_tool(self, run_id: str, tool_id: str, decision: ToolDecision, current_user: User) -> Dict[str, Any]:
        """
        Human-in-the-loop tool decision: approve, edit, or deny.
        Validates run ownership and awaiting_tool_approval status. Idempotent.
        """
        async with self.session_factory() as db:
            stmt = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            if not run:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

            if run.status != "awaiting_tool_approval":
                if run.status in ("running", "completed"):
                    return {"status": "already_processed", "run_id": run_id, "tool_id": tool_id}
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Run is not awaiting tool approval (current status: '{run.status}')",
                )

            if run_id in _resume_queues:
                await _resume_queues[run_id].put(decision)

            return {"status": "decision_accepted", "run_id": run_id, "tool_id": tool_id}

    async def cancel_run(self, run_id: str, current_user: User) -> Dict[str, Any]:
        """Cancels an active or paused run."""
        async with self.session_factory() as db:
            stmt = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            if not run:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

            run.status = "cancelled"
            await db.commit()

        await unregister_active_run(current_user.id, run_id)
        return {"status": "cancelled", "run_id": run_id}

    async def execute_run_stream(
        self,
        run_id: str,
        current_user: User,
        request: Request,
    ) -> AsyncIterator[str]:
        """
        Streams SSE events from the LangGraph cognitive loop.
        Handles interrupts for plan approval and tool approval, resuming execution cleanly.
        """
        start_time = time.perf_counter()
        seq = 0
        partial_answer = ""
        disconnected = False

        # Load run, config, and conversation history
        async with self.session_factory() as db:
            stmt = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")

            cfg_stmt = select(ChatAgentConfig).where(ChatAgentConfig.conversation_id == run.conversation_id)
            agent_cfg = (await db.execute(cfg_stmt)).scalar_one_or_none()
            enabled_agents = agent_cfg.enabled_agents if agent_cfg else ["controller", "reasoning"]
            profile = agent_cfg.model_profile if agent_cfg else "fast"
            auto_approve = agent_cfg.auto_approve_plans if agent_cfg else False

            # Load past messages
            msg_stmt = (
                select(Message)
                .where(Message.conversation_id == run.conversation_id)
                .order_by(Message.created_at)
            )
            m_res = await db.execute(msg_stmt)
            all_messages = m_res.scalars().all()

        history = [
            {"role": m.role, "content": m.content}
            for m in all_messages[:-1]
        ]
        last_msg = all_messages[-1] if all_messages else None
        last_user_prompt = last_msg.content if last_msg else ""
        file_ids = last_msg.meta.get("file_ids", []) if (last_msg and last_msg.meta) else []

        # Acquire GPU semaphore
        if gpu_worker_semaphore.locked():
            seq += 1
            queue_payload = {"type": "queued", "position": 1}
            yield f"event: queued\ndata: {json.dumps(queue_payload)}\n\n"

        async with gpu_worker_semaphore:
            # Update status to running
            async with self.session_factory() as db:
                stmt = select(Run).where(Run.id == run_id)
                r = (await db.execute(stmt)).scalar_one()
                r.status = "running"
                await db.commit()

            # Initialize LangGraph with checkpointer
            async with get_checkpointer() as checkpointer:
                graph = build_graph(checkpointer=checkpointer)

                initial_state: CogState = {
                    "user_id": current_user.id,
                    "conversation_id": run.conversation_id,
                    "run_id": run_id,
                    "user_input": last_user_prompt,
                    "file_ids": file_ids,
                    "history": history,
                    "enabled_agents": enabled_agents,
                    "profile": profile,
                    "auto_approve_plans": auto_approve,
                    "trace": [],
                }

                resume_queue = asyncio.Queue()
                _resume_queues[run_id] = resume_queue
                last_heartbeat = time.time()

                async def process_event_stream(generator) -> AsyncIterator[str]:
                    nonlocal seq, partial_answer, disconnected, last_heartbeat
                    async for event in generator:
                        try:
                            if await request.is_disconnected():
                                disconnected = True
                                logger.info("Client disconnected mid-run: %s", run_id)
                                break
                        except Exception:
                            pass

                        if event.type == "token":
                            partial_answer += event.content

                        now = time.time()
                        if now - last_heartbeat >= 15.0:
                            yield ": heartbeat\n\n"
                            last_heartbeat = now

                        seq += 1
                        event_data = event.model_dump()
                        yield f"event: {event.type}\ndata: {json.dumps(event_data)}\n\n"

                        # Persist event trace
                        async with self.session_factory() as db:
                            re_row = RunEvent(
                                run_id=run_id,
                                seq=seq,
                                type=event.type,
                                payload=event_data,
                            )
                            db.add(re_row)
                            await db.commit()

                        # 1. Handle Plan Approval Interrupt
                        if event.type == "plan_proposed" and event.requires_approval:
                            async with self.session_factory() as db:
                                r_stmt = select(Run).where(Run.id == run_id)
                                r_db = (await db.execute(r_stmt)).scalar_one()
                                r_db.status = "awaiting_plan_approval"
                                r_db.plan = event.plan.model_dump()
                                await db.commit()

                            decision: PlanDecision = await resume_queue.get()

                            async with self.session_factory() as db:
                                r_stmt = select(Run).where(Run.id == run_id)
                                r_db = (await db.execute(r_stmt)).scalar_one()
                                r_db.status = "running"
                                await db.commit()

                            resume_cmd = Command(resume=decision.model_dump())
                            async for sub_chunk in process_event_stream(
                                stream_graph_events(
                                    graph=graph,
                                    initial_state=resume_cmd,
                                    thread_id=run_id,
                                    run_id=run_id,
                                    tier=3,
                                )
                            ):
                                yield sub_chunk
                            break

                        # 2. Handle Tool Approval Interrupt
                        if event.type == "tool_proposed" and event.requires_approval:
                            async with self.session_factory() as db:
                                r_stmt = select(Run).where(Run.id == run_id)
                                r_db = (await db.execute(r_stmt)).scalar_one()
                                r_db.status = "awaiting_tool_approval"
                                await db.commit()

                            tool_dec = await resume_queue.get()

                            async with self.session_factory() as db:
                                r_stmt = select(Run).where(Run.id == run_id)
                                r_db = (await db.execute(r_stmt)).scalar_one()
                                r_db.status = "running"
                                await db.commit()

                            dec_payload = tool_dec.model_dump() if hasattr(tool_dec, "model_dump") else tool_dec
                            resume_cmd = Command(resume=dec_payload)
                            async for sub_chunk in process_event_stream(
                                stream_graph_events(
                                    graph=graph,
                                    initial_state=resume_cmd,
                                    thread_id=run_id,
                                    run_id=run_id,
                                    tier=3,
                                )
                            ):
                                yield sub_chunk
                            break

                        # 3. Handle Evaluation Record
                        if event.type == "evaluation":
                            async with self.session_factory() as db:
                                r_stmt = select(Run).where(Run.id == run_id)
                                r_db = (await db.execute(r_stmt)).scalar_one()
                                r_db.evaluation = event.model_dump()
                                await db.commit()

                        # 4. Handle Final Message Completion
                        if event.type == "final":
                            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                            async with self.session_factory() as db:
                                asst_msg = Message(
                                    id=event.message_id,
                                    conversation_id=run.conversation_id,
                                    role="assistant",
                                    content=event.content,
                                    meta={"tier": 1, "latency_ms": elapsed_ms},
                                )
                                db.add(asst_msg)

                                r_stmt = select(Run).where(Run.id == run_id)
                                r_db = (await db.execute(r_stmt)).scalar_one()
                                r_db.status = "completed"
                                r_db.latency_ms = elapsed_ms
                                await db.commit()

                try:
                    initial_gen = stream_graph_events(
                        graph=graph,
                        initial_state=initial_state,
                        thread_id=run_id,
                        run_id=run_id,
                        tier=1,
                    )
                    async for chunk in process_event_stream(initial_gen):
                        yield chunk

                except Exception as exc:
                    logger.error("Run %s failed: %s", run_id, exc, exc_info=True)
                    async with self.session_factory() as db:
                        r_stmt = select(Run).where(Run.id == run_id)
                        r_db = (await db.execute(r_stmt)).scalar_one_or_none()
                        if r_db:
                            r_db.status = "failed"
                            await db.commit()
                    err_payload = {"type": "error", "code": "run_failed", "message": f"Run failed during execution: {str(exc)}"}
                    yield f"event: error\ndata: {json.dumps(err_payload)}\n\n"

                finally:
                    if run_id in _resume_queues:
                        del _resume_queues[run_id]

                    if disconnected:
                        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                        async with self.session_factory() as db:
                            if partial_answer:
                                asst_msg = Message(
                                    conversation_id=run.conversation_id,
                                    role="assistant",
                                    content=partial_answer,
                                    meta={"interrupted": True, "latency_ms": elapsed_ms},
                                )
                                db.add(asst_msg)
                            r_stmt = select(Run).where(Run.id == run_id)
                            r_db = (await db.execute(r_stmt)).scalar_one_or_none()
                            if r_db:
                                r_db.status = "cancelled"
                                r_db.latency_ms = elapsed_ms
                                await db.commit()

                    await unregister_active_run(current_user.id, run_id)
