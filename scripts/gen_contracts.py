#!/usr/bin/env python3
"""
NEXUS Contract Generator (Step 0.4)
Generates contracts/openapi.json from Pydantic v2 schemas and FastAPI app.
"""

import json
import os
import sys

# Ensure backend is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi import FastAPI
from app.schemas.core import Principal
from app.schemas.understanding import Understanding
from app.schemas.plan import Plan, PlanStep, PlanDecision
from app.schemas.agent_config import AgentConfig
from app.schemas.run import RunCreate, FileOut, MemoryProposal, ToolProposal
from app.schemas.events import SSEEvent, RunStartedEvent, FinalEvent

app = FastAPI(
    title="NEXUS AI Cognitive System API",
    version="1.0.0",
    description="API and SSE event streaming contracts for local-first multi-agent cognitive assistant."
)

@app.post("/api/v1/runs", response_model=dict, tags=["runs"])
def create_run(run: RunCreate):
    """Start a cognitive run."""
    return {"run_id": "run_demo"}

@app.get("/api/v1/runs/{run_id}", response_model=dict, tags=["runs"])
def get_run(run_id: str):
    """Get run state and pending action."""
    return {"status": "running"}

@app.post("/api/v1/runs/{run_id}/plan", response_model=dict, tags=["runs"])
def decide_plan(run_id: str, decision: PlanDecision):
    """Submit approval, edit, or re-plan decision."""
    return {"status": "resumed"}

@app.get("/api/v1/conversations/{conversation_id}/agents", response_model=AgentConfig, tags=["agents"])
def get_agent_config(conversation_id: str):
    return AgentConfig()

@app.put("/api/v1/conversations/{conversation_id}/agents", response_model=AgentConfig, tags=["agents"])
def update_agent_config(conversation_id: str, config: AgentConfig):
    return config


def main():
    openapi_schema = app.openapi()
    target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contracts", "openapi.json"))
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Generated OpenAPI schema at: {target_path}")


if __name__ == "__main__":
    main()
