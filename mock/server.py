#!/usr/bin/env python3
"""
NEXUS Mock SSE Server (Step 0.4)
Replays 3 recorded cognitive sequences:
- Tier 1: Simple factual answer
- Tier 2: Document summary with citations
- Tier 3: Complex preparation plan with plan approval pause/resume
"""

import asyncio
import json
import time
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="NEXUS Mock API Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated in-memory runs storage
RUNS_STORE: Dict[str, Dict[str, Any]] = {}


class RunCreateReq(BaseModel):
    conversation_id: str
    message: str


class PlanDecisionReq(BaseModel):
    action: str  # approve, edit, replan
    feedback: str = None


@app.post("/api/v1/runs")
def create_run(req: RunCreateReq):
    run_id = f"run_{int(time.time())}"
    msg_lower = req.message.lower()

    if "plan" in msg_lower or "roadmap" in msg_lower or "4 month" in msg_lower:
        tier = 3
    elif "notes" in msg_lower or "document" in msg_lower or "summary" in msg_lower:
        tier = 2
    else:
        tier = 1

    RUNS_STORE[run_id] = {
        "id": run_id,
        "conversation_id": req.conversation_id,
        "message": req.message,
        "tier": tier,
        "status": "awaiting_plan_approval" if tier == 3 else "completed",
        "plan_approved": False
    }

    return {"run_id": run_id, "tier": tier}


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str):
    run = RUNS_STORE.get(run_id, {"id": run_id, "tier": 1, "status": "completed"})
    return run


@app.post("/api/v1/runs/{run_id}/plan")
def submit_plan_decision(run_id: str, decision: PlanDecisionReq):
    if run_id in RUNS_STORE:
        RUNS_STORE[run_id]["plan_approved"] = True
        RUNS_STORE[run_id]["status"] = "resumed"
    return {"status": "plan_decision_accepted", "action": decision.action}


@app.get("/api/v1/runs/{run_id}/events")
async def stream_events(run_id: str, request: Request):
    run = RUNS_STORE.get(run_id, {"tier": 1, "plan_approved": True})
    tier = run.get("tier", 1)

    async def event_generator():
        # Event 1: run_started
        yield f"event: run_started\ndata: {json.dumps({'type': 'run_started', 'run_id': run_id, 'tier': tier, 'enabled_agents': ['controller', 'reasoning']})}\n\n"
        await asyncio.sleep(0.1)

        if tier == 1:
            # TIER 1: Simple Q&A
            yield f"event: node_started\ndata: {json.dumps({'type': 'node_started', 'node': 'reasoning'})}\n\n"
            tokens = ["A ", "thread ", "is ", "a ", "lightweight ", "execution ", "unit ", "within ", "a ", "process."]
            for tok in tokens:
                yield f"event: token\ndata: {json.dumps({'type': 'token', 'content': tok})}\n\n"
                await asyncio.sleep(0.04)
            yield f"event: final\ndata: {json.dumps({'type': 'final', 'message_id': 'm_01', 'content': 'A thread is a lightweight execution unit within a process.', 'citations': []})}\n\n"

        elif tier == 2:
            # TIER 2: Document with Sources
            yield f"event: node_started\ndata: {json.dumps({'type': 'node_started', 'node': 'retrieval'})}\n\n"
            await asyncio.sleep(0.2)
            sources = [{"file": "dbms_notes.docx", "page": 44, "score": 0.91, "chunk_id": "c_dbms"}]
            yield f"event: sources\ndata: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"event: node_finished\ndata: {json.dumps({'type': 'node_finished', 'node': 'retrieval', 'summary': '1 chunk retrieved', 'ms': 140, 'status': 'ok'})}\n\n"

            yield f"event: node_started\ndata: {json.dumps({'type': 'node_started', 'node': 'reasoning'})}\n\n"
            tokens = ["According ", "to ", "your ", "DBMS ", "notes, ", "normalization ", "minimizes ", "redundancy."]
            for tok in tokens:
                yield f"event: token\ndata: {json.dumps({'type': 'token', 'content': tok})}\n\n"
                await asyncio.sleep(0.04)
            yield f"event: final\ndata: {json.dumps({'type': 'final', 'message_id': 'm_02', 'content': 'According to your DBMS notes, normalization minimizes redundancy.', 'citations': sources})}\n\n"

        else:
            # TIER 3: Complex with Plan Approval
            yield f"event: node_started\ndata: {json.dumps({'type': 'node_started', 'node': 'understanding'})}\n\n"
            await asyncio.sleep(0.1)
            und = {
                "intent": "placement_preparation",
                "domain": "Java",
                "user_context": {"year": "4th Year", "time_available": "4 Months"},
                "requirements": ["Core Java", "DSA", "DBMS", "Interviews"],
                "output_type": "Structured Roadmap",
                "complexity": "complex",
                "needs_retrieval": True,
                "needs_plan": True,
                "tools_required": [],
                "constraints": [],
                "privacy_mode": "local_only"
            }
            yield f"event: understanding\ndata: {json.dumps({'type': 'understanding', 'understanding': und})}\n\n"

            yield f"event: node_started\ndata: {json.dumps({'type': 'node_started', 'node': 'planner'})}\n\n"
            await asyncio.sleep(0.2)
            plan = {
                "goal": "4-Month Java Placement Preparation Plan",
                "steps": [
                    {"id": "step_1", "title": "Core Java refresh", "detail": "OOP, collections, streams - weeks 1-3"},
                    {"id": "step_2", "title": "DSA practice track", "detail": "arrays -> trees -> DP - weeks 2-12"},
                    {"id": "step_3", "title": "DBMS and SQL", "detail": "normalisation, joins, transactions - weeks 6-9"},
                    {"id": "step_4", "title": "Mock interviews", "detail": "HR + technical rounds - weeks 13-16"}
                ]
            }
            yield f"event: plan_proposed\ndata: {json.dumps({'type': 'plan_proposed', 'run_id': run_id, 'plan': plan, 'requires_approval': True})}\n\n"

            # Stream pauses here until approved
            while not run.get("plan_approved"):
                yield f"event: heartbeat\ndata: {json.dumps({'type': 'heartbeat', 'timestamp': int(time.time())})}\n\n"
                await asyncio.sleep(1.0)
                if await request.is_disconnected():
                    return

            # Resumed after approval
            sources = [
                {"file": "java_core.md", "page": 2, "score": 0.88, "chunk_id": "c_java"},
                {"file": "dsa_basics.md", "page": 5, "score": 0.84, "chunk_id": "c_dsa"}
            ]
            yield f"event: sources\ndata: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"event: node_started\ndata: {json.dumps({'type': 'node_started', 'node': 'reasoning'})}\n\n"
            tokens = ["Plan ", "approved. ", "Here ", "is ", "your ", "verified ", "roadmap: ", "Start ", "with ", "Java ", "OOP ", "and ", "DSA."]
            for tok in tokens:
                yield f"event: token\ndata: {json.dumps({'type': 'token', 'content': tok})}\n\n"
                await asyncio.sleep(0.04)

            yield f"event: evaluation\ndata: {json.dumps({'type': 'evaluation', 'score': 0.94, 'checks': {'coverage': True, 'citations': True}, 'retry': False})}\n\n"
            yield f"event: final\ndata: {json.dumps({'type': 'final', 'message_id': 'm_03', 'content': 'Plan approved. Here is your verified roadmap.', 'citations': sources})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
