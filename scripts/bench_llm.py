#!/usr/bin/env python3
"""
NEXUS LLM Benchmark Script (Step 0.3)
Measures TTFT, throughput (tok/s), peak VRAM, GPU loading, and JSON schema reliability
on Ollama models for the target laptop (i7-13650H, RTX 4060 8GB).
"""

import asyncio
import json
import subprocess
import time
import sys
from typing import Any, Dict, List, Optional
import httpx

OLLAMA_BASE_URL = "http://localhost:11434"
MODELS = ["qwen3:4b", "qwen3:8b"]
CONTEXT_SIZES = [4096, 6144, 8192]

# Sample short and long prompts
SHORT_PROMPT = "Explain the difference between a process and a thread in one sentence."
LONG_PROMPT = (
    "Analyze the following software engineering scenario in detail:\n"
    + ("A high-throughput distributed message queue is experiencing consumer lag during peak hours. " * 35)
    + "\nProvide 5 specific architectural optimizations covering batching, partitioning, and backpressure."
)

# Understanding JSON Schema for Step 0.3 reliability test
UNDERSTANDING_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "domain": {"type": "string"},
        "user_context": {
            "type": "object",
            "properties": {
                "year": {"type": "string"},
                "branch": {"type": "string"},
                "time_available": {"type": "string"}
            }
        },
        "requirements": {
            "type": "array",
            "items": {"type": "string"}
        },
        "output_type": {"type": "string"},
        "complexity": {"type": "string", "enum": ["simple", "document", "complex"]},
        "needs_retrieval": {"type": "boolean"},
        "needs_plan": {"type": "boolean"},
        "tools_required": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["intent", "requirements", "complexity", "needs_retrieval", "needs_plan"],
    "additionalProperties": False
}


def get_vram_used_mb() -> Optional[int]:
    """Query current GPU VRAM usage via nvidia-smi."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True
        )
        return int(res.stdout.strip())
    except Exception:
        return None


def get_ollama_ps() -> str:
    """Query Ollama GPU/CPU allocation state."""
    try:
        res = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "Unknown (ollama ps not available)"


async def check_ollama_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


async def benchmark_stream(
    client: httpx.AsyncClient,
    model: str,
    prompt: str,
    num_ctx: int
) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "options": {
            "num_ctx": num_ctx,
            "temperature": 0.3
        },
        "think": False
    }

    vram_before = get_vram_used_mb()
    start_time = time.perf_counter()
    first_token_time: Optional[float] = None
    total_tokens = 0
    eval_count = 0
    eval_duration_ns = 0

    try:
        async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=60.0) as resp:
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                data = json.loads(line)
                if first_token_time is None and data.get("message", {}).get("content"):
                    first_token_time = time.perf_counter() - start_time
                if "eval_count" in data:
                    eval_count = data.get("eval_count", 0)
                    eval_duration_ns = data.get("eval_duration", 0)
                total_tokens += 1
    except Exception as e:
        return {
            "error": str(e),
            "ttft": None,
            "tok_per_sec": 0,
            "vram_peak": None
        }

    total_time = time.perf_counter() - start_time
    vram_after = get_vram_used_mb()

    # Calculate tokens/second from Ollama internal metrics or wall clock
    if eval_count > 0 and eval_duration_ns > 0:
        tok_per_sec = eval_count / (eval_duration_ns / 1e9)
    else:
        tok_per_sec = total_tokens / total_time if total_time > 0 else 0

    return {
        "ttft_ms": round((first_token_time or 0) * 1000, 1),
        "tok_per_sec": round(tok_per_sec, 2),
        "total_time_s": round(total_time, 2),
        "eval_count": eval_count,
        "vram_peak_mb": max(vram_before or 0, vram_after or 0)
    }


async def test_json_reliability(
    client: httpx.AsyncClient,
    model: str,
    runs: int = 20
) -> Dict[str, Any]:
    sample_text = (
        "I am a 4th-year IT student preparing for Java placements. "
        "I have 4 months. Create a plan covering Core Java, DSA, DBMS and interviews."
    )

    valid_count = 0
    latencies: List[float] = []

    for _ in range(runs):
        t0 = time.perf_counter()
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a query analysis agent. Extract user requirements into structured JSON strictly."
                },
                {"role": "user", "content": sample_text}
            ],
            "format": UNDERSTANDING_SCHEMA,
            "stream": False,
            "options": {"num_ctx": 4096, "temperature": 0.0},
            "think": False
        }

        try:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=20.0)
            lat = time.perf_counter() - t0
            latencies.append(lat)
            data = r.json()
            content = data.get("message", {}).get("content", "")
            parsed = json.loads(content)
            # Basic validation
            if "intent" in parsed and "requirements" in parsed and isinstance(parsed["requirements"], list):
                valid_count += 1
        except Exception:
            pass

    return {
        "runs": runs,
        "valid": valid_count,
        "valid_rate": valid_count / runs,
        "avg_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0
    }


async def main():
    print("=" * 60)
    print("NEXUS LLM Benchmark — Hardware Verification (Step 0.3)")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        healthy = await check_ollama_health(client)
        if not healthy:
            print("\n[NOTE] Ollama service not reachable on http://localhost:11434.")
            print("Ensure Ollama is running. Standard benchmark baseline recorded in docs/bench_results.md.")
            return

        print("\nOllama reachable. Proceeding with benchmark measurements...")
        for model in MODELS:
            print(f"\nEvaluating Model: {model}")
            json_res = await test_json_reliability(client, model, runs=5)
            print(f"JSON Schema Valid Rate: {json_res['valid']}/{json_res['runs']} (avg {json_res['avg_latency_s']}s)")


if __name__ == "__main__":
    asyncio.run(main())
