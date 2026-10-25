# NEXUS — AI Cognitive System

**Local-first, multi-agent cognitive architecture for persistent, adaptive, goal-oriented reasoning.**

Built as a final-year B.E. Information Technology capstone project (Session 2026–27).

---

## Architecture Summary

NEXUS coordinates six specialized agents (`Planner`, `Retrieval`, `Reasoning`, `Memory`, `Learning`, `Evaluation`) around an on-device local model (**Qwen3** via **Ollama**) and a local vector database (**ChromaDB** with **BGE Small** ONNX embeddings).

```text
User Request 
  ──▶ Understanding (structured JSON extraction via Qwen3)
  ──▶ Executive Controller (deterministic tier classification & permission checks)
  ──▶ Memory Recall + Learning Strategy Hints
  ──▶ Planner (proposes 3–7 dependency-checked steps; pauses for user approval)
  ──▶ Retrieval (hybrid BM25 + BGE Small vector search with Reciprocal Rank Fusion)
  ──▶ Reasoning (token-budgeted grounded prompt) ⇄ Tools (AST calculator, sandbox Python with approval)
  ──▶ Evaluation (deterministic rubrics + LLM judge; bounded auto-replan loop)
  ──▶ Final Answer + Consent-based Memory Proposals + Learning Outcome Signals
```

### Three Dynamic Routing Tiers
- **Tier 1 (Simple):** Direct Reasoning only (~1 LLM call; ~400 ms).
- **Tier 2 (Document Grounded):** Understanding + Retrieval + Grounded Reasoning with inline citations (~2 LLM calls; ~1200 ms).
- **Tier 3 (Complex Synthesis):** Full Multi-Agent pipeline: Understanding + Planner + Human Checkpoint + Tools + Evaluation (~4–6 LLM calls; ~2400 ms).

---

## Hardware Budget & Resource Footprint

Optimized for an **Intel Core i7-13650H laptop with NVIDIA GeForce RTX 4060 (8 GB VRAM)** and 16 GB RAM:

| Component | Target Allocation | Peak Consumption | Notes |
|---|---|---|---|
| **Host System & Windows** | ~4 GB RAM | ~4.5 GB RAM | Background OS services |
| **PostgreSQL 16** | 1 GB RAM limit | ~180 MB RAM | Relational data & checkpointer |
| **ChromaDB (HNSW)** | ~500 MB RAM | ~320 MB RAM | Cosine vector space in memory |
| **Python Sandbox** | 512 MB RAM limit | ~120 MB RAM | Isolated sub-process container |
| **Qwen3 4B (Fast)** | ~2.6 GB VRAM | ~2.8 GB VRAM | Default model; 8,192 context window |
| **Qwen3 8B (Quality)** | ~5.5 GB VRAM | ~5.8 GB VRAM | Optional deep profile; 6,144 context window |
| **Single-GPU Semaphore** | — | — | `asyncio.Semaphore(1)` guarantees serialized generation |

---

## Quick Start (5 Commands)

```powershell
# 1. Generate cryptographically random environment secrets
powershell scripts/gen-env.ps1

# 2. Start the local Ollama server with Qwen3
ollama serve
ollama pull qwen3:4b

# 3. Verify environment diagnostics
powershell scripts/doctor.ps1

# 4. Seed system knowledge base (42 chunks across 12 files)
$env:PYTHONPATH='backend'; python backend/app/rag/seed.py

# 5. Launch the application (Backend + Frontend)
start.bat
```

Open your browser to **`http://localhost:5173`**.

---

## Monorepo Layout

```text
nexus/
├── nexus frontend/       # React 19 + TypeScript + Vite + Tailwind CSS + Framer Motion
├── backend/              # FastAPI Python backend
│   └── app/
│       ├── api/          # REST routes (auth, runs, files, memory, tools, feedback, dashboard, settings)
│       ├── agents/       # LangGraph cognitive state machine, nodes, guards, and registry
│       ├── tools/        # Safe AST calculator, scoped file reader, local search, Python client
│       ├── rag/          # FastEmbed BGE-small, Markdown chunker, BM25 hybrid retriever
│       ├── db/           # SQLAlchemy 2 async models & PostgreSQL/SQLite schema
│       ├── core/         # Security, JWT, sliding-window rate limiters, logging
│       └── schemas/      # Pydantic v2 schemas and event union
├── sandbox/              # Isolated Docker Python execution microservice
├── data/
│   ├── knowledge/        # Curated technical knowledge corpus & manifest.json
│   └── eval/             # 40-question golden evaluation set
├── docs/
│   ├── ARCHITECTURE.md   # Seminar concept mappings & algorithm mechanics
│   ├── DEMO.md           # 10-minute presentation & demo walkthrough script
│   ├── VIVA.md           # 12 technical viva examination questions & answers
│   ├── SECURITY.md       # Complete threat model & mitigations
│   ├── eval_results.md   # Ablation evaluation benchmark results
│   └── SETUP_WINDOWS.md  # Windows 11 host setup & WSL guidelines
├── scripts/              # Doctor, backup, restore, ablation benchmark, validator
├── docker-compose.yml    # Profiles: default, graph (Neo4j), monitoring (Prometheus/Grafana)
└── process.md            # Master milestone and progress tracker (100% verified)
```

---

## Test Suites & Verification

```powershell
# Run backend test suite (86/86 passing)
pytest backend/tests/ -v

# Run frontend Vitest suite (6/6 passing)
npm --prefix "nexus frontend" test -- --run

# Run frontend production build
npm --prefix "nexus frontend" run build

# Run knowledge corpus validator
python scripts/validate_knowledge.py

# Run golden set ablation benchmark
python scripts/eval_ablation.py
```
