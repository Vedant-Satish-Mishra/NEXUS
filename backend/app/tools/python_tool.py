"""
NEXUS Sandboxed Python Tool
Executes Python code inside the isolated sandbox microservice.
Requires explicit user approval before execution.
"""
import asyncio
import hashlib
import os
from pathlib import Path
import sys
from typing import Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.tools.base import ToolContext, ToolResult

# Ensure project root is in sys.path for local fallback import of sandbox.app
_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class PythonInput(BaseModel):
    code: str = Field(..., max_length=20480, description="Python code snippet to execute")
    timeout_s: Optional[float] = Field(None, ge=0.5, le=10.0, description="Optional execution timeout")


class PythonTool:
    name: str = "python"
    description: str = (
        "Executes Python code in an isolated sandbox environment (10s timeout, no network, 512MB RAM, no file access). "
        "Requires explicit user approval."
    )
    input_model = PythonInput
    requires_approval: bool = True
    timeout_s: float = 12.0

    async def run(self, ctx: ToolContext, args: PythonInput) -> ToolResult:
        code_str = args.code.strip()
        if not code_str:
            return ToolResult(status="error", output="Empty code snippet provided.", message="Empty code")

        timeout_sec = min(args.timeout_s or 10.0, 10.0)

        # 1. Attempt calling sandbox HTTP service
        headers = {"X-Sandbox-Key": settings.SANDBOX_KEY}
        payload = {"code": code_str, "timeout_s": timeout_sec}

        try:
            async with httpx.AsyncClient(timeout=timeout_sec + 1.5) as client:
                resp = await client.post(f"{settings.SANDBOX_URL}/run", json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    out = data.get("stdout", "")
                    err = data.get("stderr", "")
                    timed_out = data.get("timed_out", False)

                    if timed_out:
                        combined = (out + "\n" + err).strip()
                        return ToolResult(
                            status="error",
                            output=combined or f"Process killed: timed out after {timeout_sec} seconds.",
                            message="Timeout",
                        )

                    combined = (out + ("\n" + err if err else "")).strip()
                    if not combined:
                        combined = f"[Process finished with exit code {data.get('exit_code', 0)}]"

                    status_str = "success" if data.get("exit_code") == 0 else "error"
                    return ToolResult(status=status_str, output=combined)
        except (httpx.ConnectError, httpx.TimeoutException, Exception):
            # Fallback for local development/testing without docker compose
            pass

        # 2. Local fallback runner when sandbox container is not active
        try:
            from sandbox.app import _execute_sync

            resp_obj = await asyncio.to_thread(_execute_sync, code_str, timeout_sec)
            out = resp_obj.stdout
            err = resp_obj.stderr

            if resp_obj.timed_out:
                combined = (out + "\n" + err).strip()
                return ToolResult(
                    status="error",
                    output=combined or f"Process killed: timed out after {timeout_sec} seconds.",
                    message="Timeout",
                )

            combined = (out + ("\n" + err if err else "")).strip()
            if not combined:
                combined = f"[Process finished with exit code {resp_obj.exit_code}]"

            status_str = "success" if resp_obj.exit_code == 0 else "error"
            return ToolResult(status=status_str, output=combined)
        except Exception as e:
            return ToolResult(
                status="error",
                output=f"Sandbox execution error: {str(e)}",
                message="Sandbox error",
            )
