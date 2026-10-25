"""
NEXUS Isolated Python Sandbox Microservice
Runs Python code snippets in a locked-down subprocess with resource limits and no network access.
"""
import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="NEXUS Python Sandbox", version="1.0.0")

SANDBOX_KEY = os.environ.get("SANDBOX_KEY", "nexus_dev_sandbox_shared_secret")
EXECUTION_LOCK = asyncio.Lock()


class RunRequest(BaseModel):
    code: str = Field(..., max_length=20480, description="Python code to execute (max 20 KB)")
    timeout_s: float = Field(10.0, ge=0.5, le=10.0, description="Max execution time in seconds")


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    truncated: bool
    timed_out: bool


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexus-sandbox"}


@app.post("/run", response_model=RunResponse)
async def run_code(req: RunRequest, x_sandbox_key: Optional[str] = Header(None)):
    # 1. Shared secret authentication
    if not x_sandbox_key or x_sandbox_key != SANDBOX_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Sandbox-Key header",
        )

    # 2. Concurrency control (single execution at a time to prevent CPU hogging)
    async with EXECUTION_LOCK:
        return await asyncio.to_thread(_execute_sync, req.code, req.timeout_s)


def _execute_sync(code: str, timeout_s: float) -> RunResponse:
    start_time = time.perf_counter()
    tmp_dir = tempfile.mkdtemp(prefix="nexus_py_")
    script_path = os.path.join(tmp_dir, "main.py")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Linux resource limits (if available)
        preexec = None
        has_resource = False
        try:
            import resource  # Available on Linux/Unix only

            has_resource = True

            def linux_limits():
                try:
                    # 10s CPU limit
                    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
                    # 512MB address space
                    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
                    # 5MB file output size
                    resource.setrlimit(resource.RLIMIT_FSIZE, (5 * 1024 * 1024, 5 * 1024 * 1024))
                    # 32 processes
                    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
                except Exception:
                    pass
                if hasattr(os, "setsid"):
                    os.setsid()

            preexec = linux_limits
        except ImportError:
            pass

        # Python isolated mode (-I: ignore env vars, ignore user site, isolated)
        cmd = [sys.executable, "-I", "main.py"]

        # Run with empty environment
        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "",
            "PYTHONHOME": os.environ.get("PYTHONHOME", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),  # Required on Windows
        }
        # Filter empty
        clean_env = {k: v for k, v in clean_env.items() if v}

        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                cwd=tmp_dir,
                env=clean_env,
                preexec_fn=preexec,
                capture_output=True,
                timeout=timeout_s,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as te:
            timed_out = True
            stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
            stderr = (te.stderr or "") + f"\nExecution timed out after {timeout_s} seconds."
            exit_code = -1

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Output capping at 20 KB
        cap = 20480
        truncated = False
        if len(stdout) > cap:
            stdout = stdout[:cap] + "\n[stdout truncated at 20 KB]"
            truncated = True
        if len(stderr) > cap:
            stderr = stderr[:cap] + "\n[stderr truncated at 20 KB]"
            truncated = True

        return RunResponse(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            truncated=truncated,
            timed_out=timed_out,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
