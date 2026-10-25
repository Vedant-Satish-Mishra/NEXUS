"""
NEXUS Tool Execution Loop & Human Approval Checkpoint
Step 4.B.2 — Execute loop and sandboxed Python with approval
"""
import logging
import uuid
from typing import Any, Dict, List, Optional
from langgraph.types import StreamWriter, interrupt
from pydantic import BaseModel, Field

from app.agents.registry import guarded, traced
from app.core.llm import LLMProvider, default_llm_provider
from app.schemas.core import Principal
from app.tools import TOOLS, executor
from app.tools.base import ToolContext

logger = logging.getLogger("nexus.agents.execute")

ALLOWED_TOOLS = ["calculator", "file_reader", "local_search", "python"]


class ToolDecisionOutput(BaseModel):
    needed: bool = Field(..., description="Whether a tool execution is required to answer accurately")
    tool: Optional[str] = Field(None, description="Tool name: 'calculator', 'file_reader', 'local_search', or 'python'")
    input: Optional[str] = Field(None, description="Input string, expression, query, or code for the tool")
    reason: Optional[str] = Field(None, description="Reason why this tool is being invoked")


def should_check_tools(state: Dict[str, Any]) -> bool:
    """Only inspect tools if Understanding or Plan explicitly required tools."""
    tools_req = state.get("understanding", {}).get("tools_required", [])
    if tools_req:
        return True

    plan = state.get("plan", {})
    steps = plan.get("steps", [])
    for step in steps:
        if step.get("tool"):
            return True

    return False


@traced("tool_decide")
async def tool_decide_node(
    state: Dict[str, Any],
    writer: StreamWriter,
    llm: Optional[LLMProvider] = None,
) -> Dict[str, Any]:
    """
    Decides whether a tool is needed. Ordinary queries without tools_required
    in Understanding or Plan bypass this with zero LLM calls.
    """
    iterations = state.get("tool_iterations", 0)
    if iterations >= 3 or not should_check_tools(state):
        return {"pending_tool_call": None}

    # If tools are required, use structured LLM call
    provider = llm or default_llm_provider
    user_input = state.get("user_input", "")
    existing_tools = state.get("tool_calls", [])

    system_prompt = (
        "You are the NEXUS Tool Dispatcher. Available tools:\n"
        "- calculator: mathematical expressions (e.g. '17.5% * 2480', 'sqrt(144)')\n"
        "- file_reader: reads user files by file_id (e.g. '{\"file_id\": \"...\"}')\n"
        "- local_search: searches local documents with hybrid retrieval (e.g. 'DBMS indexing')\n"
        "- python: executes Python code in sandbox for complex algorithms, data analysis, or simulations.\n\n"
        "If the query requires calculation, search, reading an uploaded file, or python execution, "
        "and has not already been answered by past tool calls, select the tool and provide its input. "
        "Otherwise set needed=false."
    )

    user_prompt = f"User query: {user_input}\n"
    if existing_tools:
        user_prompt += f"Previous tool executions: {existing_tools}\n"

    try:
        decision: ToolDecisionOutput = await provider.structured(
            schema=ToolDecisionOutput,
            prompt=user_prompt,
            system=system_prompt,
        )

        if decision.needed and decision.tool in ALLOWED_TOOLS and decision.input:
            tool_id = f"tool_{uuid.uuid4().hex[:8]}"
            return {
                "pending_tool_call": {
                    "tool_id": tool_id,
                    "tool": decision.tool,
                    "input": decision.input,
                    "reason": decision.reason or "",
                }
            }
    except Exception as e:
        logger.warning(f"tool_decide failed, continuing without tool: {e}")

    return {"pending_tool_call": None}


@traced("tool_propose")
async def tool_propose_node(
    state: Dict[str, Any],
    writer: StreamWriter,
) -> Dict[str, Any]:
    """Emits tool_proposed event if a tool was decided."""
    call = state.get("pending_tool_call")
    if not call:
        return {}

    tool_name = call["tool"]
    tool_obj = TOOLS.get(tool_name)
    req_approval = tool_obj.requires_approval if tool_obj else False

    if writer:
        writer(
            {
                "type": "tool_proposed",
                "tool_id": call["tool_id"],
                "tool": tool_name,
                "input": call["input"],
                "requires_approval": req_approval,
            }
        )

    return {}


async def tool_wait_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Approval checkpoint for approval-gated tools (e.g. Python).
    Unapproved tools pass through automatically.
    """
    call = state.get("pending_tool_call")
    if not call:
        return {"tool_decision": None}

    tool_name = call["tool"]
    tool_obj = TOOLS.get(tool_name)

    if not tool_obj or not tool_obj.requires_approval:
        return {"tool_decision": {"action": "approve"}}

    # Interrupt and wait for user decision
    decision = interrupt(
        {
            "type": "tool_proposed",
            "run_id": state.get("run_id"),
            "tool_id": call["tool_id"],
            "tool": tool_name,
            "input": call["input"],
            "reason": call.get("reason", ""),
        }
    )
    # decision: {action: "approve" | "edit" | "deny", code?: str, input?: str}
    return {"tool_decision": decision}


@traced("tool_run")
async def tool_run_node(
    state: Dict[str, Any],
    writer: StreamWriter,
) -> Dict[str, Any]:
    """
    Executes the tool using ToolExecutor and records results in CogState.
    """
    call = state.get("pending_tool_call")
    if not call:
        return {}

    decision = state.get("tool_decision") or {"action": "approve"}
    action = decision.get("action", "approve")
    tool_name = call["tool"]
    tool_id = call["tool_id"]

    # 1. Denied path
    if action == "deny":
        if writer:
            writer(
                {
                    "type": "tool_result",
                    "tool_id": tool_id,
                    "tool": tool_name,
                    "output": "Execution denied by user.",
                    "ms": 0,
                    "status": "denied",
                }
            )

        new_call_rec = {
            "tool_id": tool_id,
            "tool": tool_name,
            "input": call["input"],
            "output": "Execution denied by user.",
            "status": "denied",
        }
        current_calls = list(state.get("tool_calls", []))
        current_calls.append(new_call_rec)
        return {
            "tool_calls": current_calls,
            "tool_iterations": state.get("tool_iterations", 0) + 1,
            "pending_tool_call": None,
            "tool_decision": None,
        }

    # 2. Approved or Edited path
    input_to_run = call["input"]
    if action == "edit":
        input_to_run = decision.get("code") or decision.get("input") or input_to_run

    principal = Principal(
        user_id=state.get("user_id", "default"),
        conversation_id=state.get("conversation_id", "default"),
    )
    ctx = ToolContext(principal=principal, run_id=state.get("run_id", "default"))

    res = await executor.execute(
        name=tool_name,
        raw_args=input_to_run,
        ctx=ctx,
        allowed_tools=ALLOWED_TOOLS,
        approved_by_user=(action in ("approve", "edit")),
    )

    if writer:
        writer(
            {
                "type": "tool_result",
                "tool_id": tool_id,
                "tool": tool_name,
                "output": res.output,
                "ms": res.duration_ms,
                "status": "ok" if res.status == "success" else "error",
            }
        )

    new_call_rec = {
        "tool_id": tool_id,
        "tool": tool_name,
        "input": input_to_run,
        "output": res.output,
        "status": res.status,
        "duration_ms": res.duration_ms,
    }

    current_calls = list(state.get("tool_calls", []))
    current_calls.append(new_call_rec)

    return {
        "tool_calls": current_calls,
        "tool_iterations": state.get("tool_iterations", 0) + 1,
        "pending_tool_call": None,
        "tool_decision": None,
    }


def route_after_tool_run(state: Dict[str, Any]) -> str:
    """After tool execution, decide if another tool is needed or proceed to reasoning."""
    iterations = state.get("tool_iterations", 0)
    if iterations < 3 and state.get("pending_tool_call"):
        return "tool_decide"
    return "reason"
