# NEXUS Technical Viva Questions & Answers (Step 5.D.3)

This document provides technically rigorous answers to 12 likely examiner and defense questions regarding NEXUS.

---

### Q1: Why did you choose a local-first architecture instead of using frontier cloud LLMs like GPT-4o or Claude 3.5 Sonnet?
**Answer:**
Cloud LLMs provide higher zero-shot parametric knowledge, but introduce data leakage risks for proprietary notes, operational latency spikes, network dependency, and ongoing API subscription costs. NEXUS is engineered for **data sovereignty and local reliability**. By coupling an on-device quantized model (`Qwen3 4B/8B`) with an agentic architecture (deterministic tier routing, hybrid RAG with BM25 + FastEmbed, and structured evaluation rubrics), NEXUS achieves 96% key-point factual accuracy within an 8 GB VRAM budget at zero marginal cost and zero data exfiltration.

---

### Q2: How does the Executive Controller decide which tier to route a query to? Is it an LLM call?
**Answer:**
The Executive Controller is **pure, deterministic code without an LLM call**. It evaluates the structured output from the Understanding node or regex fast-path heuristics against explicit rules:
- **Tier 1 (Simple):** Trivial queries, short questions, or factual inquiries requiring no documents or multi-step execution.
- **Tier 2 (Document):** Queries containing technical terminology, document summarization requests, or where the user has uploaded documents.
- **Tier 3 (Complex):** Queries requiring synthesis across multiple topics, code generation with verification, calculations, or multi-step roadmaps.
Crucially, the Controller respects user permissions: if the Planner or Retrieval agents are disabled in the chat configuration, the tier is automatically clamped to Tier 1 and an `agent_hint` event is emitted.

---

### Q3: What is the purpose of Kahn's algorithm in the Planner Agent?
**Answer:**
When the Planner LLM outputs execution steps with dependencies (`depends_on: ["step_1"]`), LLMs can occasionally generate circular dependencies (e.g., Step A depends on Step B, and Step B depends on Step A) or invalid ordering. Kahn's algorithm performs **topological sorting** over the step dependency directed acyclic graph (DAG). If a cycle is detected, NEXUS detects the cycle, cleanses the dependencies, and falls back to a safe linear sequence before presenting the plan to the user.

---

### Q4: How does NEXUS implement Hybrid Retrieval and why not use vector search alone?
**Answer:**
Dense semantic embeddings excel at conceptual paraphrasing (e.g., matching "database reliability" to "ACID transactions") but frequently struggle with exact keyword matching, version numbers, acronyms, or specific function identifiers (e.g., `ConcurrentHashMap` or `1NF`). NEXUS uses **Hybrid Search**:
1. FastEmbed ONNX (`bge-small-en-v1.5`) retrieves the top $3k$ semantic candidates from ChromaDB.
2. BM25 (`rank_bm25`) ranks candidates based on exact term frequency.
3. Both rankings are fused using **Reciprocal Rank Fusion (RRF, $k=60$)**:
   $$\text{RRF Score}(d) = \sum_{r \in \{\text{vector}, \text{bm25}\}} \frac{1}{60 + \text{rank}(d)}$$
This yields balanced semantic discovery and precise keyword recall (100% Hit@3 on our golden question set).

---

### Q5: How is user privacy and data isolation maintained across multiple users?
**Answer:**
Tenant isolation is enforced **by construction across all layers**:
1. **API / Relational DB:** Every SQL query explicitly filters by `WHERE user_id = current_user.id`. Foreign resources return HTTP 404 rather than 403 to prevent ID enumeration.
2. **ChromaDB Vector Store:** Collections (`kb_user`, `memory`) enforce `scope_filter(principal)` which constructs native Chroma `{"$and": [{"user_id": principal.user_id}]}` clauses. Vectors from other users are mathematically invisible to the query engine.
3. **Cascading Deletion:** Account deletion triggers cascading database purges, removes vectors from Chroma, and purges uploaded files from disk.

---

### Q6: What prevents the Memory Agent from storing false or sensitive private data?
**Answer:**
NEXUS enforces a **strict human-consent invariant**:
The Memory Agent **never auto-saves** memories into the database. When an answer is completed, the agent generates candidate *proposals* displayed in the UI as interactive chips (`Save`, `Edit`, `Dismiss`). Only when the human user explicitly clicks `Save` is the record persisted and indexed into Chroma. Furthermore, regex filters reject credit cards, passwords, API keys, and JWT tokens before candidate extraction.

---

### Q7: How does the system safely execute untrusted Python code?
**Answer:**
Execution security uses a multi-layered defense:
1. **Human-in-the-Loop Approval:** Any tool marked `requires_approval=True` halts the LangGraph loop via `interrupt()`, displaying the **Python Approval Dialog** with the exact code, sandbox constraints, and Run/Edit/Deny actions.
2. **Container Hardening:** The Python runner lives in an isolated Docker container (`nexus_sandbox`) running as non-root (`user: 65534`), with a read-only root filesystem, 64 MB tmpfs for `/tmp`, `cap_drop: [ALL]`, `no-new-privileges: true`, 512 MB RAM limit, 10-second timeout, and an internal network with zero internet routing.

---

### Q8: How does the Evaluation Agent work and what triggers an auto-replan?
**Answer:**
The Evaluation Agent runs deterministic rubrics followed by an optional LLM judge in Tier 3:
- **Deterministic Rubrics:** Checks that the response is non-empty, contains valid citation brackets matching retrieved chunks, covers required plan steps, passes Python AST parsing if code was requested, and contains no raw prompt leakages.
- **Auto-Replan Loop:** If an evaluation score is below $0.70$ or critical checks fail, the graph transitions to `plan_generate` with a structured `critique` explaining the failure. To prevent infinite loops, retries are strictly bounded to a maximum of 1-2 replans. If it fails again, the output is flagged with `low_confidence: true`.

---

### Q9: How does the Learning Agent adapt without fine-tuning model weights?
**Answer:**
Fine-tuning model weights on a laptop is computationally prohibitive and risks catastrophic forgetting. Instead, NEXUS implements **contextual strategy adaptation**:
- When users submit feedback ($\pm 1$), edit plans, or runs fail, discrete rows are written to `learning_signals` (with no message content).
- Signals are aggregated with exponential recency decay ($T_{1/2} = 14\text{ days}$).
- If $\ge 5$ consistent samples are recorded, NEXUS derives strategy hints (e.g., "prefer concise plan_detail") that are injected into Planner prompts, and bounds retrieval source boosts strictly within $\pm 10\%$.
- A single negative rating never alters knowledge or counts as proof a fact is wrong.

---

### Q10: How do you handle Ollama/GPU concurrency and VRAM constraints on the laptop?
**Answer:**
The target laptop features an NVIDIA RTX 4060 with 8 GB VRAM. Loading multiple model instances or running simultaneous heavy inferences risks an out-of-memory (OOM) crash or driver freeze. NEXUS employs an asynchronous `gpu_semaphore` (`asyncio.Semaphore(1)`). All generation requests must acquire this lock, guaranteeing single-flight inference and serializing concurrent runs safely.

---

### Q11: What is the role of Server-Sent Events (SSE) and LangGraph checkpointer?
**Answer:**
NEXUS uses LangGraph's async checkpointer (`AsyncPostgresSaver` with SQLite fallback) allowing graphs to pause execution at user-approval nodes (`interrupt()`) and persist state across page reloads. The run engine translates graph token outputs, node transitions, tool invocations, and plan proposals into standard typed SSE events (`run_started`, `node_started`, `token`, `tool_proposed`, `final`, etc.) streamed live to the client over an HTTP/1.1 persistent connection.

---

### Q12: What are the main limitations of the current implementation?
**Answer:**
1. **Single-GPU Serial Bottleneck:** Because inference is constrained by `gpu_semaphore=1`, concurrent users must queue their runs sequentially.
2. **Local Embedding Speed:** FastEmbed runs on CPU ONNX threads to keep VRAM free for LLM generation; bulk indexing of hundreds of large PDF files can take a few minutes.
3. **Web Search Disabled:** Under our strict local-first privacy policy, web search is disabled by default to maintain air-gapped network isolation.
