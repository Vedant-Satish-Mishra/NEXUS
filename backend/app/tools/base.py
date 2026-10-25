"""
NEXUS Tool Base Protocol, Context, and Executor
Provides the Tool protocol, ToolContext, ToolResult, and ToolExecutor.
Enforces validation, permission guards, timeouts, output size caps, and audit logging.
"""
import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Type, runtime_checkable
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.core import Principal
from app.db.models import ToolExecution


@dataclass
class ToolContext:
    principal: Principal
    run_id: str
    db: Optional[Any] = None  # AsyncSession or async_sessionmaker


class ToolResult(BaseModel):
    status: str  # "success", "error", "denied"
    output: str
    duration_ms: int = 0
    message: Optional[str] = None


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    input_model: Type[BaseModel]
    requires_approval: bool
    timeout_s: float

    async def run(self, ctx: ToolContext, args: BaseModel) -> ToolResult:
        ...


class ToolExecutor:
    """Registry and runner for all tools with strict validation and audit trails."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "requires_approval": t.requires_approval,
                "timeout_s": t.timeout_s,
            }
            for t in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        raw_args: Any,
        ctx: ToolContext,
        allowed_tools: Optional[List[str]] = None,
        approved_by_user: bool = False,
    ) -> ToolResult:
        start_time = time.perf_counter()

        # 1. Verify existence
        tool = self._tools.get(name)
        if not tool:
            res = ToolResult(
                status="error",
                output=f"Tool '{name}' is not registered.",
                message="Unknown tool",
            )
            await self._audit(ctx, name, raw_args, res, approved_by_user, 0)
            return res

        # 2. Check permission / allowed for this run
        if allowed_tools is not None and name not in allowed_tools:
            res = ToolResult(
                status="error",
                output=f"Tool '{name}' is not allowed for this run.",
                message="Tool not permitted",
            )
            await self._audit(ctx, name, raw_args, res, approved_by_user, 0)
            return res

        # 3. Validate arguments against Pydantic schema
        try:
            if isinstance(raw_args, str):
                try:
                    parsed_raw = json.loads(raw_args)
                except Exception:
                    parsed_raw = {"expression": raw_args} if name == "calculator" else {"query": raw_args}
            elif isinstance(raw_args, dict):
                parsed_raw = raw_args
            elif isinstance(raw_args, BaseModel):
                parsed_raw = raw_args.model_dump()
            else:
                parsed_raw = dict(raw_args)

            validated_args = tool.input_model.model_validate(parsed_raw)
        except (ValidationError, Exception) as val_err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolResult(
                status="error",
                output=f"Invalid arguments for tool '{name}': {str(val_err)}",
                duration_ms=duration_ms,
                message="Validation failed",
            )
            await self._audit(ctx, name, raw_args, res, approved_by_user, duration_ms)
            return res

        # 4. Enforce timeout and run
        try:
            res = await asyncio.wait_for(tool.run(ctx, validated_args), timeout=tool.timeout_s)
        except asyncio.TimeoutError:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolResult(
                status="error",
                output=f"Tool '{name}' timed out after {tool.timeout_s} seconds.",
                duration_ms=duration_ms,
                message="Timeout exceeded",
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            res = ToolResult(
                status="error",
                output=f"Tool execution failed: {str(e)}",
                duration_ms=duration_ms,
                message="Execution error",
            )

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        res.duration_ms = duration_ms

        # 5. Cap output size at 20 KB (20,480 chars)
        max_output_len = 20480
        if len(res.output) > max_output_len:
            res.output = res.output[:max_output_len] + "\n[Output truncated at 20 KB limit]"

        # 6. Audit logging
        await self._audit(ctx, name, raw_args, res, approved_by_user, duration_ms)
        return res

    async def _audit(
        self,
        ctx: ToolContext,
        name: str,
        raw_args: Any,
        res: ToolResult,
        approved_by_user: bool,
        duration_ms: int,
    ) -> None:
        if not ctx.db:
            return

        session = ctx.db
        close_session = False
        if hasattr(ctx.db, "begin") and not hasattr(ctx.db, "execute"):
            session = ctx.db()
            close_session = True

        try:
            input_str = raw_args if isinstance(raw_args, str) else json.dumps(raw_args, default=str)
            record = ToolExecution(
                run_id=ctx.run_id,
                tool=name,
                input=input_str[:10000],
                output=res.output[:20480],
                status=res.status,
                approved_by_user=approved_by_user,
                duration_ms=duration_ms,
            )
            session.add(record)
            await session.commit()
        except Exception:
            # Audit failures shouldn't crash tool result
            pass
        finally:
            if close_session:
                await session.close()
