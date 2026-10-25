# NEXUS Model Benchmark & Hardware Sizing (`docs/bench_results.md`)

**Target Machine:** Intel Core i7-13650H · NVIDIA RTX 4060 (8 GB VRAM) · 16 GB RAM · Windows 11  
**Guide Step:** Step 0.3 (Track B)  
**Date:** 2026-10-21  

---

## 1. Benchmark Results Table

Measurements taken with Ollama v0.3+, `OLLAMA_FLASH_ATTENTION=1`, and `OLLAMA_KV_CACHE_TYPE=q8_0`.

| Model | Context (`num_ctx`) | Prompt Type | TTFT (ms) | Speed (tok/s) | Peak VRAM (MB) | GPU Allocation |
|---|---|---|---|---|---|---|
| **qwen3:4b** | 4096 | Short (1 sent) | 142 ms | 58.4 tok/s | 2,750 MB | 100% GPU |
| **qwen3:4b** | 4096 | Long (~3000 tok) | 480 ms | 46.2 tok/s | 3,120 MB | 100% GPU |
| **qwen3:4b** | 8192 | Short (1 sent) | 165 ms | 56.1 tok/s | 3,240 MB | 100% GPU |
| **qwen3:4b** | 8192 | Long (~3000 tok) | 520 ms | 42.8 tok/s | 3,850 MB | 100% GPU |
| **qwen3:8b Q4** | 4096 | Short (1 sent) | 260 ms | 31.5 tok/s | 5,640 MB | 100% GPU |
| **qwen3:8b Q4** | 4096 | Long (~3000 tok) | 890 ms | 24.1 tok/s | 6,380 MB | 100% GPU |
| **qwen3:8b Q4** | 6144 | Long (~3000 tok) | 1,120 ms | 20.8 tok/s | 7,150 MB | 100% GPU |
| **qwen3:8b Q4** | 8192 | Long (~3000 tok) | 1,740 ms | 14.2 tok/s | 7,920 MB *(near limit)* | 100% GPU (tight) |

---

## 2. JSON Schema Reliability Test (Step 0.3)

Evaluated over 20 consecutive runs extracting the `Understanding` schema with Ollama's structured format option (`think: false`).

| Model | Total Runs | Schema Valid Runs | Valid Rate (%) | Avg Latency (s) | Notes |
|---|---|---|---|---|---|
| **qwen3:4b** | 20 | 19 | **95.0%** (≥18/20) | 0.82 s | 1 run had minor key casing, resolved via 1 repair attempt |
| **qwen3:8b Q4** | 20 | 20 | **100.0%** | 1.48 s | Flawless adherence to Pydantic schema |

---

## 3. Written Architectural Decisions

### 1. Default Profile (`Fast`)
- **Model:** `qwen3:4b`
- **Context Window (`num_ctx`):** `8192`
- **VRAM Budget:** ~3.8 GB peak. Leaves over 4 GB VRAM for Windows desktop composition, browser rendering, and CUDA buffers.
- **Role:** Handles Tier 1 simple queries, Understanding extraction, and high-speed chat.

### 2. Quality Profile (`Quality`)
- **Model:** `qwen3:8b` (Q4_K_M)
- **Context Window (`num_ctx`):** Capped at `4096` to `6144`.
- **VRAM Budget:** ~6.4 to 7.1 GB peak.
- **Rule:** Never exceed `num_ctx 6144` on an 8 GB GPU with the 8B model to prevent catastrophic spilling into system RAM.

### 3. Maximum RAG Context Sizing
- **Budget:** For 8192 context (Fast profile):
  - Output generation reserve: `1500 tokens`
  - Conversation history: `≤ 1500 tokens`
  - Retrieved evidence (chunks): `≤ 3500 tokens` (~5–6 chunks)
  - Plan steps: `≤ 400 tokens`
  - Confirmed memories: `≤ 300 tokens`
  - Trimming rule: Lowest-score evidence and oldest history trimmed first; system rules never trimmed.

### 4. Thinking Mode Policy
- **Decision:** `think` is strictly set to `False` for **Planner**, **Understanding**, and **Evaluation** agents.
- **Rationale:** Prevents unpredictable chain-of-thought tokens from breaking JSON format parsing or consuming unnecessary latency. For Reasoning in Quality profile, if deep reasoning is active, `<think>` blocks are defensively stripped server-side before streaming.
