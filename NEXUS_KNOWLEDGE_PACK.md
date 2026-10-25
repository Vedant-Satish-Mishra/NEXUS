# NEXUS Knowledge Pack — short to big, for answering questions about the project

| | |
|---|---|
| **File** | `docs/NEXUS_KNOWLEDGE_PACK.md` (human-readable) and `data/nexus_qa.jsonl` (262 chat-format Q&A pairs) — both generated from the same source, so they always agree |
| **Date** | 2026-10-18 |
| **Facts come from** | `docs/PRD.md`, `docs/PAGE_SPECIFICATIONS.md`, `nexus_implementation_guide.md` v2.0, the seminar deck and the owner's recorded decisions |
| **Status of the project** | Planning documented, **implementation not started**. Repository **not inspected**. |

## 0. How to use this pack

| Option | What you do | When to choose it |
|---|---|---|
| **1. RAG (recommended)** | Put this file in `data/knowledge/` so NEXUS indexes it into the knowledge base | The model must answer with facts; facts can be updated by editing this file |
| **2. Context / system prompt** | Paste section 1 (answering rules) plus the short and medium parts into any LLM's context | Quick use with any chat model |
| **3. Fine-tune (optional)** | Train a small model on `data/nexus_qa.jsonl` | Only to teach *answer style and length*; see section 6 |

## 1. Answering rules (give these to the other model)

```text
You are the NEXUS Project Assistant. Answer questions about the NEXUS AI Cognitive System using only the project facts you were taught. Match the requested length: 'one sentence' or no length hint -> short or medium; 'in full detail' -> structured bullet list. Label proposals as proposed and undecided items as undecided. If a fact is not known or not decided, say so plainly; never invent features, numbers, files, endpoints or credentials. NEXUS is AGI-inspired and never claimed to be AGI.
```

Length levels used throughout this pack:

| Level | Length | Use when the question says |
|---|---|---|
| **Short** | 1 sentence | "in one line", "briefly", "what is…" |
| **Medium** | 3-5 sentences | no hint, or "explain" |
| **Long** | structured bullets | "in detail", "everything about…", "viva answer" |

Tags inside answers: **proposed** = recommended but not yet approved by the owner; **undecided** = no decision exists; **unverified** = comes from a report or assumption, not from code.

## 2. Level 1 — Short answers (one sentence each)

| # | Question | Short answer |
|---|---|---|
| 1 | What is NEXUS? | NEXUS is a local-first, multi-agent AI cognitive system that answers from your own documents and confirmed memories on your own laptop. |
| 2 | Is NEXUS an AGI? | No. NEXUS is AGI-inspired and explicitly does not claim to be AGI. |
| 3 | What research question does NEXUS answer? | It asks how independent AI capabilities can be unified into a cognitive architecture for persistent, adaptive, goal-oriented behaviour. |
| 4 | What problems does NEXUS solve? | It targets context loss, weak planning, limited memory, poor tool selection, hallucination without self-correction, and fragmented AI capabilities. |
| 5 | What are the objectives of NEXUS? | Integrate research techniques into one framework, decompose queries, retrieve with RAG, plan and reason, use memory and tools, and verify outputs. |
| 6 | What is the architecture of NEXUS? | An Executive Controller routes each request through Planner, Memory, Retrieval and Learning agents into a Reasoning LLM, then an Evaluation Agent checks it before the final response. |
| 7 | What does the Executive Controller do? | The Executive Controller is plain code that classifies each request into a tier and routes it, without an LLM call. |
| 8 | What are the routing tiers? | Tier 1 simple uses Reasoning only, Tier 2 document adds Understanding and Retrieval, Tier 3 complex uses all enabled agents with plan approval, tools and Evaluation. |
| 9 | What is the NEXUS pipeline? | Understand, Plan, Retrieve, Reason, Execute, Verify, Respond. |
| 10 | What is the Understanding step? | A structured LLM call converts the user's message into a validated JSON object that guides planning and retrieval. |
| 11 | How does the Planner work? | The Planner turns the goal into 3-7 ordered steps and pauses so the user can edit, approve or re-plan before anything else runs. |
| 12 | What does the Retrieval Agent do? | The Retrieval Agent searches the knowledge base and the user's permitted files, issuing one focused query per requirement or plan step. |
| 13 | How does RAG work in NEXUS? | NEXUS embeds text with BGE Small, stores vectors in ChromaDB, and combines semantic and keyword (BM25) search before the model answers. |
| 14 | What does the Reasoning Agent do? | The Reasoning Agent is a dedicated component that builds the prompt from plan, memories and evidence and uses Qwen3 to produce the answer. |
| 15 | How does NEXUS memory work? | No. NEXUS only proposes memories; nothing is saved until the user confirms it. |
| 16 | What does the Learning Agent learn? | The Learning Agent adapts strategies and ranking from feedback, evaluation scores and task outcomes; it never changes model weights. |
| 17 | What does the Evaluation Agent do? | The Evaluation Agent checks every answer with rules and, for complex tasks, one LLM judge pass, and triggers a bounded retry if the score is low. |
| 18 | Which tools can NEXUS use? | Calculator, file reader, local knowledge search and sandboxed Python; web search is optional and off by default. |
| 19 | How is Python execution made safe? | Python runs in a separate isolated service with no network, strict limits and per-run user approval; code never runs on the host. |
| 20 | Can users choose which agents run? | Yes. Before the first message of a chat the user picks agents or a preset; Controller and Reasoning are always on. |
| 21 | Which LLM does NEXUS use and why local? | NEXUS uses Qwen3 through Ollama locally: 4B by default and 8B Q4 as an optional quality mode; it does not train or fine-tune a model. |
| 22 | What hardware does NEXUS target? | The target is an i7-13650H laptop with an RTX 4060 (8 GB VRAM), 16 GB RAM and a 512 GB SSD running Windows. |
| 23 | What is the technology stack? | React + TypeScript, FastAPI, Ollama + Qwen3, LangGraph, BGE Small, ChromaDB, PostgreSQL, JWT and Docker; Neo4j and Grafana optional. |
| 24 | Which files can NEXUS read? | PDF, DOCX, TXT, Markdown, PPTX, XLSX, CSV and source code, plus images through OCR. |
| 25 | How does NEXUS protect privacy? | No. Data is isolated per user and conversation, and nothing leaves the machine unless the user enables an external tool. |
| 26 | What pages does NEXUS have? | Login, Register, Chat, Knowledge, Memory, Workflows, Tools, Dashboard and Settings, in the existing themed glass UI with smooth animations. |
| 27 | How does login work in NEXUS? | Email and password with JWT: a short-lived access token plus a refresh token in an HttpOnly cookie. |
| 28 | How is NEXUS deployed? | Ollama runs on the Windows host; the backend, PostgreSQL and sandbox run in Docker; the frontend runs locally during development. |
| 29 | How is the team organised? | A four-person team split into four tracks: frontend and animations, agents and LangGraph, RAG and ingestion, backend/auth/deployment. |
| 30 | What are the project milestones? | A preparation phase plus five milestones; the MVP is the end of Milestone 2 with PDF and DOCX upload. |
| 31 | Which algorithms does NEXUS use? | Not exactly: it uses Chroma's HNSW instead of FAISS, BM25 instead of a separate TF-IDF, dependency-graph ordering instead of A*, and a rule-based controller as the decision tree. |
| 32 | What are the main risks? | Model memory limits, invalid JSON from small models, sandbox abuse, prompt injection, cross-user leaks and scope creep, each with a planned mitigation. |
| 33 | How will NEXUS be evaluated? | With a 40-question golden set measuring retrieval hit-rate, answer coverage, refusal on unanswerable questions, latency and an ablation across presets and models. |
| 34 | What is not included in NEXUS? | Model training, subscriptions and billing, audio and video, default web search, vision models, and any AGI claim. |
| 35 | What is still undecided? | Repository details, guest mode, domain scope, review date, supported browsers and ten proposed technical decisions (D1-D10) are still unconfirmed. |
| 36 | How does a paused plan survive a restart? | Runs are checkpointed in PostgreSQL by LangGraph, so a paused plan or tool approval can resume after a refresh or restart. |

## 3. Level 2 — Medium answers (a short paragraph each)

### 3.1 Identity
**Q:** What is NEXUS?

NEXUS (proposed expansion: Networked Executive for eXtensible Understanding and Self-learning) is a final-year B.E. IT project. An Executive Controller coordinates six agents (Planner, Retrieval, Reasoning, Memory, Learning, Evaluation) around a local Qwen3 model served by Ollama. It turns a request into structured JSON, plans, retrieves evidence, reasons, evaluates and responds, while the user controls plans, memories and code execution.

### 3.2 AGI claim
**Q:** Is NEXUS an AGI?

The seminar conclusion states that NEXUS does not claim to be AGI. It is an experimental framework for investigating the architectural prerequisites of persistent, general-purpose and adaptive machine intelligence by embedding LLMs in a structured cognitive control loop.

### 3.3 Research question
**Q:** What research question does NEXUS answer?

Modern components such as vector databases, API calling and reasoning frameworks are widely available, but most LLM interactions stay stateless (prompt in, response out) and lack continuity, self-monitoring and purposeful progress. NEXUS investigates how to unify these pieces into one architecture.

### 3.4 Problems solved
**Q:** What problems does NEXUS solve?

LLMs lose context across sessions, struggle to decompose complex goals, cannot reliably reuse past experience, may pick the wrong tool, can produce unverified output, and exist as separate capabilities. NEXUS answers with memory, planning with user approval, a permission-checked tool registry, RAG with citations plus evaluation, and one orchestrated architecture.

### 3.5 Objectives
**Q:** What are the objectives of NEXUS?

Owner objectives: integrate techniques from selected papers; understand and decompose queries into tasks; retrieve knowledge with RAG, semantic and keyword search; apply planning and reasoning; use memory, agents and tools per task; verify and evaluate outputs. Seminar objectives add AGI-inspired intelligence, cognitive integration, accuracy, adaptive decisions, and privacy with scalability.

### 3.6 Architecture
**Q:** What is the architecture of NEXUS?

The block diagram flows User (goal) -> LLM input interpretation -> Executive Controller (LangGraph) -> Planner / Memory / Retrieval / Learning agents -> Reasoning LLM (Qwen3) -> Evaluation Agent -> Final Response, with a loop from Evaluation back to the Planner. In the implementation plan the Planner runs before Retrieval because the user must approve the plan first.

### 3.7 Executive Controller
**Q:** What does the Executive Controller do?

It reads the Understanding JSON and simple message features, picks Tier 1, 2 or 3, orders the pipeline steps, and clamps the route to the agents the user enabled. If a disabled agent would help, it emits a hint instead of running it.

### 3.8 Routing tiers
**Q:** What are the routing tiers?

Tiering keeps NEXUS responsive on a laptop. A simple factual question costs about one LLM call, a document question about two, and a complex planning task about four to six. The tier is limited by the agents the user enabled for that chat.

### 3.9 Pipeline
**Q:** What is the NEXUS pipeline?

The Controller decides which steps are needed. Simple questions skip planning and execution; complex tasks use planning, retrieval, tools and verification. Tier 3 order: Understanding -> Controller -> Memory and Learning (code) -> Planner -> user approval -> Retrieval -> Reasoning with tools -> Evaluation -> Final answer -> memory proposals.

### 3.10 Understanding step
**Q:** What is the Understanding step?

For example, 'I am a 4th-year IT student preparing for Java placements, 4 months, plan Java, DSA, DBMS and interviews' becomes JSON with intent placement_preparation, domain Java, user_context (year, branch, time_available), requirements and an output type. It runs only when Retrieval or Planner is enabled and the message is non-trivial.

### 3.11 Planner and plan approval
**Q:** How does the Planner work?

For complex tasks the plan appears as editable step cards. The user can edit, reorder, add or delete steps, approve, approve-and-do-not-ask-again for that chat, or request a re-plan with feedback. The run is paused using a LangGraph interrupt and stored in a PostgreSQL checkpointer, so it survives a page refresh or backend restart.

### 3.12 Retrieval Agent
**Q:** What does the Retrieval Agent do?

It builds up to five queries from the approved plan steps or the Understanding requirements (falling back to the raw message), searches with hybrid retrieval, merges and de-duplicates chunks, drops weak matches and returns at most about six chunks with file, page and score. It uses no LLM call.

### 3.13 RAG and search
**Q:** How does RAG work in NEXUS?

Documents are parsed, chunked (about 250-350 words with overlap), embedded with BAAI/bge-small-en-v1.5 and stored in ChromaDB with metadata. At query time vector candidates and BM25 candidates are fused with Reciprocal Rank Fusion. Answers cite sources as [n], and if the evidence is insufficient the model says so instead of guessing.

### 3.14 Reasoning Agent
**Q:** What does the Reasoning Agent do?

Qwen3 is the underlying model; the Reasoning Agent is the software component that manages how it is used. It assembles the context within a token budget, instructs the model to cite sources and admit insufficient evidence, streams the answer, and can loop with tools up to three times.

### 3.15 Memory
**Q:** How does NEXUS memory work?

There are three levels: short-term (current run state), long-term (stable facts and preferences) and episodic (past tasks and outcomes). The Memory Agent recalls relevant confirmed memories by similarity, importance and recency, and after an answer it proposes new ones as Save / Edit / Dismiss chips.

### 3.16 Learning Agent
**Q:** What does the Learning Agent learn?

It records aggregated signals (no message content) such as ratings, evaluation scores, whether a plan was approved unchanged or edited, and tool success. After enough samples it produces short hints for the Planner and Reasoning prompts and small retrieval ranking boosts. A single negative rating never changes knowledge.

### 3.17 Evaluation Agent
**Q:** What does the Evaluation Agent do?

Deterministic checks cover non-empty answers, valid citations, plan and requirement coverage, code that parses and numbers that match calculator results. For Tier 3 a single structured LLM judge scores groundedness, relevance and completeness. Below a threshold (about 0.7) it re-plans automatically, at most once by default and never more than twice; then it returns the best answer with a low-confidence flag.

### 3.18 Tools
**Q:** Which tools can NEXUS use?

Every tool has a schema, timeout, permission check and audit record. Tool calls come only from the Reasoning agent's structured output, validated against an allow-list and the run's needs. The calculator uses a safe expression evaluator, the file reader reads only the user's own parsed files, and Python always needs per-run user approval.

### 3.19 Python sandbox
**Q:** How is Python execution made safe?

The sandbox is its own container on an internal Docker network with no internet access, running as a non-root user with a read-only filesystem, a small temporary directory, dropped capabilities, a 10-second timeout and memory, CPU and process limits. The Docker socket is never mounted.

### 3.20 Agent selection and presets
**Q:** Can users choose which agents run?

Fast enables Reasoning only, Balanced enables Reasoning, Retrieval, Memory and Evaluation, and Full enables all six. Changes apply from the next message, never mid-run, and the backend enforces the stored choice so a request cannot enable a disabled agent.

### 3.21 Models and local inference
**Q:** Which LLM does NEXUS use and why local?

Local inference gives privacy and no per-token cost. One model serves every agent to avoid slow model swapping on an 8 GB GPU. Training is excluded because it is impractical on this hardware and not needed: RAG, memory and orchestration provide the behaviour.

### 3.22 Hardware budget
**Q:** What hardware does NEXUS target?

Ollama runs on the Windows host to use the GPU; FastAPI, PostgreSQL and the sandbox run in Docker with WSL 2 memory capped around 5 GB. Neo4j is off by default because it needs 1.5 GB or more. OCR runs on the CPU so it does not take VRAM from Qwen3.

### 3.23 Technology stack
**Q:** What is the technology stack?

Each choice follows the seminar slide: component-based typed UI, high-performance async Python with OpenAPI, private local inference with no per-token cost, graph-based agent orchestration, lightweight local embeddings, a simple embedded vector database, reliable relational storage, stateless authentication and reproducible containers.

### 3.24 Files and ingestion
**Q:** Which files can NEXUS read?

Files are validated, stored privately, parsed in the background, chunked with page references, embedded and indexed. Scanned PDFs and images use CPU OCR. Each file shows processing, ready or failed with a reason, and deleting a file removes its chunks and vectors.

### 3.25 Privacy and isolation
**Q:** How does NEXUS protect privacy?

Local model, local embeddings and local storage keep content on the machine. Every route checks ownership and returns Not found for others' resources, and every retrieval builds its scope filter internally from the user's identity. Deleting a file, memory or account removes derived data too.

### 3.26 UI and pages
**Q:** What pages does NEXUS have?

The UI keeps the Aurora/Ocean glass look and other themes, adds a live agent graph, a plan-approval panel, citation chips, tool cards and memory proposal chips, and respects reduced motion. The mockup uses a warm orange and deep-brown palette with sketch-style outlines.

### 3.27 Authentication
**Q:** How does login work in NEXUS?

Passwords are hashed, access tokens last about 30 minutes and are kept in memory by the frontend, refresh tokens last about 7 days. Every resource is owned by a user and checked on the backend. There are no subscriptions or admin console.

### 3.28 Deployment
**Q:** How is NEXUS deployed?

Docker Compose provides profiles: default (PostgreSQL, backend, sandbox), graph (Neo4j) and monitoring (Prometheus and Grafana). Scripts handle start, migrate, seed, backup and an environment check.

### 3.29 Team and workflow
**Q:** How is the team organised?

Work follows contracts first: API paths, event types and schemas are agreed before parallel development, with branches named feat/<track>-<step>, protected main, code owners per directory and one cross-track review per pull request.

### 3.30 Milestones and MVP
**Q:** What are the project milestones?

Milestone 1 core foundation, 2 cognitive pipeline, 3 knowledge and memory, 4 tools and reliability, 5 complete application. The guide has 51 numbered steps across four tracks, and the tracker is updated after every milestone.

### 3.31 Seminar algorithms vs implementation
**Q:** Which algorithms does NEXUS use?

The seminar slide lists NLP/LLM, BM25 + TF-IDF, embeddings + cosine, FAISS, embedding-based memory, A*/graph search, a decision tree, multi-step reasoning and feedback scoring. The implementation matches most and deviates on FAISS, TF-IDF, A* and the learned decision tree, and these deviations should be stated honestly in the report.

### 3.32 Main risks
**Q:** What are the main risks?

Long contexts can push the model out of VRAM, so context is capped and budgeted. Small models can break JSON, so schema-constrained output with repair and fallback is used. Code runs in an isolated sandbox with approval. Retrieved text is untrusted. Isolation is tested with automated two-user checks. A milestone plan with an MVP limits scope.

### 3.33 Evaluation and testing
**Q:** How will NEXUS be evaluated?

The guide plans retrieval metrics (hit at 1/3/5, MRR, false-retrieval rate), an ablation comparing a plain LLM with Balanced and Full presets on 4B and optionally 8B, plus automated security and authorization tests. Numeric targets in the PRD are provisional until benchmarks produce real figures.

### 3.34 Out of scope
**Q:** What is not included in NEXUS?

Also excluded in v1 (proposed): Google OAuth, e-mail verification, password reset, non-English languages, a complex admin console and medical, legal or financial advice features.

### 3.35 Open decisions
**Q:** What is still undecided?

The website repository has not been inspected, so the real framework, pages and components are unknown. Proposed decisions include fastembed for embeddings, sandbox libraries, learning-data policy, auth scope, concurrency, CI, MVP cut line, English-only and deferred extensions.

### 3.36 Pause and resume
**Q:** How does a paused plan survive a restart?

The graph pauses with an interrupt and stores state under a thread id equal to the run id. The decision endpoint resumes it with the user's choice. Duplicate decisions resume once, events are stored with sequence numbers so a dropped stream can replay, and stale paused runs expire.

## 4. Level 3 — Big answers (full detail)

### 4.1 Identity
**Q:** What is NEXUS?

- Name: NEXUS, AI Cognitive System (proposed full form: Networked Executive for eXtensible Understanding and Self-learning; tagline 'where agents connect to think').
- Kind: web application with a React + TypeScript frontend and a FastAPI backend.
- Core idea: unify independent AI capabilities (retrieval, reasoning, memory, planning, agents, evaluation) into one cognitive architecture for persistent, adaptive, goal-oriented behaviour.
- Pipeline: Understand -> Plan -> Retrieve -> Reason -> Execute -> Verify -> Respond.
- Runs locally on the owner's laptop (i7-13650H, RTX 4060 8 GB, 16 GB RAM, Windows) with Ollama + Qwen3.
- Private by default: no user content leaves the machine unless the user enables an external tool.
- Academic context: final-year B.E. Information Technology seminar/project, session 2026-27, under a faculty guide, built by a four-person team.
- Status: requirements, page specifications, implementation guide and tracker are written; implementation has not started.

### 4.2 AGI claim
**Q:** Is NEXUS an AGI?

- Seminar conclusion: the bottleneck for highly autonomous, reliable systems is no longer just model size but architectural organization.
- NEXUS shows that embedding LLMs in a structured control loop can synthesize independent capabilities into a cohesive, goal-directed system.
- 'AGI-inspired' means the functional requirements of AGI (memory, reasoning, learning, adaptation) inspire the design; it does not mean human-level intelligence.
- Rule: no document, UI text or demo may claim AGI.
- Defensible contributions: tiered routing, user-approved planning, evaluator-driven bounded retry, feedback-informed learning, consent-based memory.

### 4.3 Research question
**Q:** What research question does NEXUS answer?

- Introduction slide points: modern AI components are available; LLMs are transactional; persistence is missing; AGI aims at robust learning, reasoning and adaptation; AGI's functional requirements can inspire current system design.
- Research question: How can independent AI capabilities be unified into a cognitive architecture for persistent, adaptive, goal-oriented behavior?
- Answer approach: an Executive Controller plus specialised agents, retrieval grounding, multi-level memory, tools, evaluation and learning, all on a local model.
- Evidence base: seminar literature review (RAG by Lewis et al. 2020, ReAct by Yao et al. 2022, Generative Agents by Park et al. 2023, LangGraph, Ollama + Qwen3, ChromaDB + BGE, FastAPI + React).

### 4.4 Problems solved
**Q:** What problems does NEXUS solve?

- Context loss / limited memory -> multi-level memory (short-term, long-term, episodic) with user-confirmed saves.
- Planning limitation / complex tasks -> query decomposition and a Planner whose plan the user approves.
- Tool and agent selection -> Executive Controller with rules, and a tool registry with permission checks.
- Reliability / hallucination -> RAG with citations, 'not in the material' behaviour, Evaluation Agent with bounded retry.
- Fragmented capabilities and no end-to-end workflow -> one pipeline: Understand -> Plan -> Retrieve -> Reason -> Execute -> Verify -> Respond.
- Single-model dependency (owner's list) -> specialised prompts, contracts and tools per agent on one local model; the model is replaceable behind an interface.
- Note: the seminar deck and the owner's later list word the problems differently; which wording is canonical for the report is undecided.

### 4.5 Objectives
**Q:** What are the objectives of NEXUS?

- O1 integrate techniques from the selected research papers into one framework.
- O2 understand and decompose user queries into tasks and subtasks.
- O3 retrieve relevant knowledge using RAG, semantic search and keyword retrieval.
- O4 apply planning and reasoning for systematic multi-step problem solving.
- O5 use memory, agents and tools according to each task.
- O6 verify and evaluate outputs to improve reliability, relevance and accuracy.
- Seminar objectives: AGI-inspired intelligence (human-like reasoning), cognitive integration (memory + retrieval + reasoning), accuracy (reduce hallucination with RAG), adaptive decisions, privacy and scalability (secure, modular system).

### 4.6 Architecture
**Q:** What is the architecture of NEXUS?

- Frontend: React + TypeScript. Backend: FastAPI (async). Orchestration: LangGraph with a PostgreSQL checkpointer so paused runs resume.
- Models: Ollama + Qwen3 (4B default, 8B Q4 optional). Embeddings: BGE Small. Vector store: ChromaDB. Relational store: PostgreSQL.
- Executive Controller is code, not an LLM call; it classifies the request into a tier and routes it.
- Agents: Planner, Retrieval, Reasoning, Memory, Learning, Evaluation. Reasoning is a dedicated agent with its own prompt and contract on the same Qwen3 model.
- Deviation from the diagram: the diagram fans out in parallel; the plan uses Planner first (user approves), then Retrieval, because queries come from the approved plan and a single GPU gains nothing from parallelism.
- Evaluation can send work back to the Planner, limited to 1-2 automatic retries.
- Optional components: Neo4j (relationship memory) and Grafana (monitoring), both off by default.

### 4.7 Executive Controller
**Q:** What does the Executive Controller do?

- Inputs: Understanding JSON (complexity, needs_retrieval, needs_plan, tools_required) and message features (length, attachments, keywords such as plan, roadmap, schedule, compare).
- Hard rules: attached files or phrases like 'my notes' mean at least Tier 2; plan-like keywords or about 30 or more words mean Tier 3.
- Permission clamp: complex needs Planner else downgrade to document or simple; document needs Retrieval else downgrade.
- Output: tier and an ordered route containing only enabled agents.
- It is the orchestrator, not another worker agent; coordination runs through LangGraph.
- Equivalent to a hand-built decision tree of rules; there is no learned tree.

### 4.8 Routing tiers
**Q:** What are the routing tiers?

- Tier 1 Simple (e.g., 'What is a HashMap?'): Reasoning only, about 1 LLM call.
- Tier 2 Document (e.g., 'Summarize my uploaded DBMS notes'): Understanding + Retrieval + Reasoning (+ rule-based checks), about 2 calls.
- Tier 3 Complex (e.g., 'Create a 4-month Java placement plan'): all enabled agents, plan approval, tools, Evaluation, about 4-6 calls.
- Code, not LLM calls, do routing, JSON validation, calculation, permission checks, ranking and memory recall.
- No fixed response time is promised; speed depends on prompt length, context size and generated tokens.

### 4.9 Pipeline
**Q:** What is the NEXUS pipeline?

1. Understand: turn the message into validated JSON (only when Retrieval or Planner is enabled and the message is non-trivial).
2. Plan: Planner proposes 3-7 steps; the user edits, approves or asks to re-plan.
3. Retrieve: one focused query per requirement or plan step; hybrid semantic + keyword search.
4. Reason: Qwen3 answers using plan, memories, evidence and strategy hints, citing sources as [n].
5. Execute: tools run only when needed (calculator, file reader, local search, sandboxed Python with approval).
6. Verify: Evaluation runs deterministic checks and, for Tier 3 only, one LLM judge; low scores trigger a bounded automatic re-plan.
7. Respond: final answer, citations, memory proposals for the user to confirm, learning record.

### 4.10 Understanding step
**Q:** What is the Understanding step?

- Fields: intent, domain, user_context, requirements, output_type, complexity (simple|document|complex), needs_retrieval, needs_plan, tools_required, constraints, privacy_mode.
- Seminar example output: intent placement_preparation; domain Java; user_context {year 4th Year, branch IT, time_available 4 Months}; requirements [Core Java, DSA, DBMS, Interview Preparation]; output_type 4-month preparation plan.
- Generated with schema-constrained structured output, then validated by Pydantic.
- Failure handling: one repair attempt, then a safe rule-based fallback; malformed JSON never crashes the pipeline or bypasses access controls.
- Skipped for trivial messages and for the Fast preset, so Tier 1 under Fast makes zero Understanding calls.
- The JSON drives the Planner and one retrieval query per requirement.

### 4.11 Planner and plan approval
**Q:** How does the Planner work?

- Plan schema: goal plus steps (id, title, detail, depends_on, needs_retrieval, optional tool); 1-8 steps, acyclic dependencies, topologically ordered.
- Two graph nodes: plan_generate (the LLM call) and plan_wait (no side effects, calls interrupt) because a resumed node re-executes from its start.
- Decisions: approve, edit (user's steps replace the plan after validation), replan (limited to 3 user re-plans).
- Auto-approve switch per chat; simple questions never show a plan.
- Evaluation-triggered re-planning is automatic, shows a notice and is limited to 1-2 attempts.
- Paused runs expire after about 24 hours (proposed).
- 'Graph search' from the seminar slide is implemented as dependency-graph validation and ordering, not A*.

### 4.12 Retrieval Agent
**Q:** What does the Retrieval Agent do?

- Query sources in order: approved plan steps with needs_retrieval, then Understanding.requirements, then the raw message.
- Example: a Java placement request yields separate queries for Core Java, DSA, DBMS and interviews.
- Scope filters: system (read-only knowledge), personal and chat; built from the user's identity inside the code, never from raw request filters.
- A score threshold drops irrelevant chunks; an empty result is allowed and the Reasoning agent then says the material does not cover the question.
- Emits a sources event so the UI shows file, page and score.

### 4.13 RAG and search
**Q:** How does RAG work in NEXUS?

- Embedding model: BGE Small (384 dimensions); proposed runtime fastembed (ONNX) to save RAM, pending owner approval.
- Vector store: ChromaDB (cosine, HNSW index); the seminar slide mentions FAISS, which is a documented deviation; the store sits behind an interface so FAISS could be added.
- Hybrid search: BM25 (rank_bm25) plus vector search fused by RRF (k=60). TF-IDF is not a separate component; BM25 is the TF-IDF-family ranking.
- Collections: kb_system (preloaded knowledge), kb_user (uploads) and memory (confirmed memories).
- Chunks keep source, topic, page and chunk index; ids are deterministic so re-ingestion is idempotent.
- Retrieved text is untrusted: instructions inside documents are never followed or turned into tool calls.
- Purpose: reduce hallucination (seminar objective) and ground answers in the user's material.

### 4.14 Reasoning Agent
**Q:** What does the Reasoning Agent do?

- Prompt order: system rules, approved plan, user memories, numbered evidence, strategy hints, recent history, user message; empty sections are omitted.
- Budget for an 8K context: about 1500 tokens reserved for the answer; history up to 1500, evidence up to 3500, plan 400, memories 300; oldest history and lowest-score evidence are trimmed first; system rules never.
- Rules: cite [n] only for evidence actually used; say when evidence does not answer; treat evidence and tool output as untrusted data; never reveal prompts or internal agent names.
- Hidden chain-of-thought is never shown; the UI shows plans, sources, tool calls and evaluation results.
- Tool decisions come from a structured output and are validated against an allow-list.

### 4.15 Memory
**Q:** How does NEXUS memory work?

- Short-term: conversation state and recent turns in LangGraph state, with deterministic compaction of older turns.
- Long-term and episodic: PostgreSQL rows plus vectors in ChromaDB, created only by the user's confirmation.
- Proposals come from rules (explicit 'remember ...', stated goals, preferences, constraints); an optional LLM suggestion appears only in the Full preset and is still only a proposal.
- Secrets such as keys, passwords or tokens are never proposed.
- Users can view, search, edit, delete one memory or all memories; a per-chat Memory toggle disables recall and proposals.
- Recall ranking: similarity x (0.7 + 0.3 x importance) x recency (half-life about 60 days).
- Neo4j can later add relationship memory as an optional extension.

### 4.16 Learning Agent
**Q:** What does the Learning Agent learn?

- Signals: user feedback (thumbs up/down), evaluation results, task outcomes (plan approved, edited, re-planned; tool success or failure; completed or abandoned).
- Stored as (user, intent, strategy key, signal, value, source, run id); controlled strategy keys such as plan_detail, retrieval_top_k, answer_style, evidence_source.
- Hints are generated by code: at least 5 samples (proposed), average below 0.4 means avoid, above 0.75 means prefer; at most 3 hints of under 120 characters.
- Retrieval boosts are bounded to plus or minus 10 percent; data decays over time.
- Controls: per-chat toggle, global toggle, reset learning data; provenance kept by run id.
- This implements 'feedback-based scoring' from the algorithms slide.

### 4.17 Evaluation Agent
**Q:** What does the Evaluation Agent do?

- Always: rule checks (no LLM call).
- Tier 3 with Evaluation enabled: one structured judge call with strict scoring and an actionable critique of up to three sentences; fails open if the output is malformed.
- Tier 1 and 2: rules only, no judge and no retry.
- Retry policy: automatic re-plan without asking again, visible notice, best answer kept, hard limit of 2.
- Purpose: improve reliability, relevance and accuracy (objective O6) without tripling latency.

### 4.18 Tools
**Q:** Which tools can NEXUS use?

- Calculator: AST-based, numbers and basic operators only; rejects names, attribute access and explosive exponents.
- File reader: input is a file id and page range owned by the user; no filesystem paths.
- Local search: the hybrid retriever with the run's identity.
- Python: executed only in the isolated sandbox service after the user clicks Run, Edit and Run, or Deny.
- Web search: explicit opt-in tool, off by default, clearly marked when used, planned for later.
- Maximum 3 tool iterations per run; every call is audited.
- Injection defence: text in documents or tool output is never parsed for tool calls.

### 4.19 Python sandbox
**Q:** How is Python execution made safe?

- Interface: POST /run with code (up to about 20 KB) and a timeout of at most 10 seconds; shared-secret header; one run at a time.
- Limits: memory about 512 MB, CPU 1, processes capped, output capped at 20 KB per stream, new process group killed on timeout.
- Libraries: standard library plus numpy (proposed); no access to user files in v1.
- Approval: the user sees the code, can edit it, and must press Run; denied code never executes.
- A keyword blocklist is not treated as security; isolation is the control.
- Security tests: infinite loop, memory bomb, network attempt, writing outside the temp dir, fork bomb, environment inspection, reaching other services.

### 4.20 Agent selection and presets
**Q:** Can users choose which agents run?

- Locked on: Executive Controller and Reasoning.
- Toggleable: Planner, Retrieval, Memory, Learning, Evaluation.
- The first run is refused (HTTP 412) until a configuration exists, so the setup panel cannot be skipped.
- The configuration is stored per conversation and snapshotted at run start.
- If a disabled agent would have helped, the UI shows a dismissible hint such as 'Enable Planner for better results'.
- Also selectable: model profile Fast (Qwen3 4B) or Quality (Qwen3 8B Q4) and auto-approve plans.

### 4.21 Models and local inference
**Q:** Which LLM does NEXUS use and why local?

- Qwen3 4B needs about 2.5 GB for weights; Qwen3 8B Q4 about 5.2 GB; the KV cache grows with context (reduced with q8_0).
- Fast profile: qwen3:4b, context 8192. Quality profile: qwen3:8b, context 4096-6144.
- Ollama settings: flash attention on, KV cache q8_0, one loaded model, no parallel requests, keep-alive 10 minutes.
- Structured outputs use Ollama's JSON-schema format option; thinking mode is off for planner and evaluator.
- The LLM sits behind an LLMProvider interface so another provider can replace it.
- Fine-tuning is optional and only for style or format; facts belong in RAG.

### 4.22 Hardware budget
**Q:** What hardware does NEXUS target?

- VRAM: 4B profile comfortable; 8B profile fits but is tight and needs a shorter context.
- RAM plan (approximate): Windows 4-5 GB, browser and IDE 3-4 GB, Docker/WSL about 5 GB, Ollama host process about 1 GB.
- Embeddings via ONNX (proposed) instead of PyTorch save roughly 1 GB.
- Single GPU means sequential LLM calls and a global worker queue; one active run per user (proposed).
- Only the owner's laptop is a verified target; other hardware is unverified.
- Real numbers come from a benchmark script (tokens per second, VRAM, first-token time).

### 4.23 Technology stack
**Q:** What is the technology stack?

- Frontend: React + TypeScript (component UI, strong typing). Animations: Framer Motion; agent graph: React Flow (proposed).
- Backend: FastAPI (async, OpenAPI). Database access: SQLAlchemy 2 async + Alembic.
- AI: Ollama + Qwen3; LangGraph for agent state; BGE Small embeddings; ChromaDB for RAG and semantic memory.
- Data: PostgreSQL for users, conversations, runs, files, memories, feedback and checkpoints.
- Auth: JWT access token plus refresh cookie; passwords hashed.
- Ops: Docker Compose; Neo4j (relationship queries) and Grafana (metrics) optional.
- The existing frontend's bundler and structure are unverified because the repository was not available.

### 4.24 Files and ingestion
**Q:** Which files can NEXUS read?

- Code types: Python, Java, JavaScript, TypeScript, HTML, CSS, SQL.
- Parsers: PDF text per page (OCR only for pages without a text layer), DOCX headings and tables, PPTX slides and notes, XLSX and CSV header-aware rows.
- Limits (proposed): 25 MB per file, 500 MB per user; extension allow-list and content-type sniffing.
- Scopes: chat-only by default, optional promotion to a personal knowledge base, plus a read-only preloaded knowledge base.
- Audio, video and vision-model understanding are out of v1; OCR is the image path.
- Chunks of about 250-350 words with overlap; deterministic ids make re-ingestion idempotent.

### 4.25 Privacy and isolation
**Q:** How does NEXUS protect privacy?

- Isolation invariant: retrieval functions take the user and conversation identity and construct filters themselves; no public function accepts a raw filter.
- Memory is saved only with consent and can be deleted at any time.
- Web search, if ever enabled, is opt-in and clearly marked.
- Prompt-injection hygiene: retrieved text and tool output are untrusted data.
- Learning data stores scores only, with a reset control (proposed).
- Passwords are hashed; refresh tokens live in an HttpOnly cookie.

### 4.26 UI and pages
**Q:** What pages does NEXUS have?

- Routes: /login, /register, /chat, /chat/:id, /knowledge, /memory, /workflows, /workflows/:runId, /tools, /dashboard, /settings, plus a not-found page.
- Chat is the main workspace: new-chat setup panel, messages, understanding card, plan approval, tool cards, composer, and the agent graph panel.
- Agent graph nodes: Understanding, Controller, Memory, Learning, Planner, Retrieval, Execute, Reasoning, Evaluation, Final; states idle, active, waiting, done, skipped, disabled, error.
- Animations: route transitions, message entry, list changes, skeleton loaders; only transform and opacity are animated; reduced motion makes everything instant.
- Existing features to keep (reported, unverified): theme engine, voice input, suggestion cards, font size and glass settings.
- Removed: subscriptions, billing, mock admin console and mock data.

### 4.27 Authentication
**Q:** How does login work in NEXUS?

- Endpoints: register, login, refresh, logout, me.
- Same generic error for unknown email and wrong password; rate limits on login and registration.
- Excluded in v1 (proposed): Google OAuth, e-mail verification, password reset.
- The legacy mock auth stored passwords in plain text and is replaced.
- Guest access (the legacy 3-message limit) is undecided.

### 4.28 Deployment
**Q:** How is NEXUS deployed?

- WSL 2 memory capped (about 5 GB) via .wslconfig; containers reach Ollama through host.docker.internal.
- The sandbox is on an internal-only network; the Docker socket is never mounted.
- First run: generate environment secrets, start the stack, pull the Qwen3 model in Ollama, seed the preloaded knowledge base.
- Production-style profile: nginx serving the built frontend with proxy buffering off so streaming works.
- A public hosted deployment is undecided and a GPU host would be needed for Qwen3.

### 4.29 Team and workflow
**Q:** How is the team organised?

- Track A Frontend & Animations; Track B Agents & LangGraph; Track C RAG & Ingestion; Track D Backend, Auth & Deployment.
- Pydantic models are the source of truth; OpenAPI and TypeScript types are generated; a mock server lets the frontend work before the backend.
- Definition of done: code merged, tests passing, acceptance check shown, tracker updated, no secrets.
- Contract changes need approval from all four tracks.
- Names of owners per track are not assigned in the documents.

### 4.30 Milestones and MVP
**Q:** What are the project milestones?

- Preparation: repository, environment, model benchmark, contracts, frontend audit, knowledge corpus plan.
- M1: backend, auth, streaming chat, minimal LangGraph with checkpointer, embedder and vector store.
- M2: understanding, controller tiers, planner with approval, retrieval, reasoning, agent selection UI, agent graph.
- M3: all file parsers, OCR, hybrid retrieval, memory with confirmation, Knowledge and Memory pages.
- M4: tools, sandbox, Evaluation Agent, feedback, Workflows and Tools pages.
- M5: Learning Agent, dashboard, settings, polish, ablation evaluation, packaging, security and documentation.
- No fixed deadline exists; the date of the first faculty review is not yet known.

### 4.31 Seminar algorithms vs implementation
**Q:** Which algorithms does NEXUS use?

- Query understanding: Qwen3 structured JSON (matches).
- Knowledge retrieval: BM25 inside hybrid search (TF-IDF not separate).
- Semantic retrieval: BGE Small + cosine in Chroma (matches).
- Fast vector search: Chroma HNSW, not FAISS; FAISS can plug in behind the interface.
- Memory management: embedding similarity with importance and recency plus consent (matches).
- Planning: LLM plan with dependency validation and topological ordering, not A*.
- Decision making: explicit rule-based controller, equivalent to a hand-built decision tree.
- Reasoning: Reasoning agent with bounded tool loop (matches).
- Learning: aggregated feedback scoring with thresholds and decay (matches).

### 4.32 Main risks
**Q:** What are the main risks?

- VRAM spill: context caps, flash attention, q8_0 KV cache, 4B default.
- Invalid JSON: structured outputs, validation, one repair, rule-based fallback.
- Interrupt re-execution: separate generate and wait nodes.
- Lost paused runs: PostgreSQL checkpointer.
- Docker memory pressure: WSL cap, Neo4j off by default, ONNX embeddings.
- Sandbox escape: separate service, internal network, non-root, read-only filesystem, dropped capabilities, no Docker socket, per-run approval.
- Prompt injection: untrusted evidence, tool calls only from validated structured output.
- Cross-user leakage: isolation by construction and an authorization test matrix.
- Unwanted memories: consent before saving.
- Evaluation retries slowing answers: rules first, one judge, retry limit.
- Library API drift: pin versions and verify against current documentation.

### 4.33 Evaluation and testing
**Q:** How will NEXUS be evaluated?

- Golden set: 40 questions across simple, document-grounded, planning and adversarial/unanswerable cases.
- Retrieval: hit@k, MRR, false-retrieval rate; regression test in CI.
- Ablation metrics: key-point coverage, citation correctness, refusal rate, latency p50/p95, LLM calls per answer, retry rate, evaluator score, peak VRAM.
- Provisional targets: hit@3 at or above 0.80, false retrieval at or below 0.20, Stop within 2 seconds.
- Honest limits: small sample, automatic scoring bias, single machine.

### 4.34 Out of scope
**Q:** What is not included in NEXUS?

- Excluded by the owner: model training or fine-tuning; subscriptions, payments, billing and a complex admin console; audio and video; vision understanding (OCR only); web search by default; Neo4j and Grafana as required parts.
- Proposed exclusions pending approval: OAuth, e-mail verification, password reset, multilingual support.
- Medical advice is treated as out of scope until the owner decides, because the project was formerly called Doctor Chatbot / MedAssist.
- Mobile apps and public internet hosting are not requested.

### 4.35 Open decisions
**Q:** What is still undecided?

- Repository: not inspected; legacy claims are unverified.
- Canonical problem-statement wording (seminar vs owner's list).
- Domain: general technical study, placement preparation only, or any medical use.
- Guest mode and the legacy 3-message limit; default landing route after login.
- Business or adoption goals: none stated.
- Date of the first faculty review and any marking rubric; supported browsers and breakpoints.
- Proposed decisions D1-D10: embedding runtime, sandbox libraries, learning data, frontend baseline, auth scope, concurrency, repo and CI, MVP cut line, language, deferred extensions.
- When something is undecided, an answering model must say so instead of guessing.

### 4.36 Pause and resume
**Q:** How does a paused plan survive a restart?

- Run states: queued, running, awaiting plan approval, awaiting tool approval, completed, failed, cancelled, expired.
- Resume uses Command(resume=decision) with thread id equal to run id.
- The node that calls interrupt has no side effects; the LLM call lives in a separate node.
- Server-sent events carry node, token, plan, tool, evaluation and final events plus a heartbeat every 15 seconds.
- Last-Event-ID replay restores a dropped connection.
- Specific LangGraph API details must be verified against the pinned version.

## 5. Questions the model must answer with "not known / not decided"

These teach the model **not to guess**.

| Question | Correct answer |
|---|---|
| What bundler and router does the existing frontend repository use? | I do not know. The repository was not available, so the framework details, routes and components are unverified. Please provide the repository. |
| What is the deadline for the project demo? | No fixed deadline has been set. The first faculty review date is not yet known, so milestones are used instead. |
| Which hospital data does NEXUS use? | NEXUS does not use hospital data. The project was formerly named Doctor Chatbot / MedAssist, and medical advice is treated as out of scope until the owner decides otherwise. |
| How many users has NEXUS got? | No adoption numbers exist. NEXUS has no business or user-count goals stated and implementation has not started. |
| Has NEXUS been implemented? | No. Requirements, page specifications, an implementation guide and a tracker are written, but implementation has not started; progress is 0 percent in the tracker. |
| Does NEXUS use GPT-4 or a cloud API? | No. It is designed to run local Qwen3 models through Ollama, with no external API by default. |
| Is NEXUS better than ChatGPT? | I cannot claim that. NEXUS is an experimental local architecture; its contribution is measured with a planned evaluation, and no results exist yet. |
| What accuracy does NEXUS achieve? | No measured accuracy exists yet. The PRD lists provisional targets, such as hit@3 of at least 0.80, to be validated by benchmarks after implementation. |
| Who owns each track? | The documents do not assign names to tracks, so I cannot say. |
| Does NEXUS support Hindi or Marathi? | Not in v1. English-only is proposed because BGE Small is an English model; multilingual support would be a later extension. |

## 6. Fine-tuning notes (honest guidance)

- **Dataset:** `data/nexus_qa.jsonl`, one JSON object per line with `messages` (system, user, assistant), plus `topic` and `level`. Totals: 262 pairs — short 82, medium 108, long 72. Average answer length in words: short 20, medium 45, long 100.
- **What fine-tuning can do here:** teach tone, length control (one line vs detailed) and the habit of saying "not decided". **What it cannot do reliably:** make a small model memorise ~36 topics of facts from about 260 examples. For facts, use RAG (option 1).
- **Hardware reality:** training is not done by Ollama. On an RTX 4060 with 8 GB VRAM, parameter-efficient training (LoRA/QLoRA) of a small model such as Qwen3 4B with short sequences is usually feasible, but you must verify memory use with your chosen tool (for example Unsloth or Hugging Face TRL) and then convert/serve the result yourself. Do this *after* the NEXUS implementation milestones, not before.
- **Suggested process:** (1) split by topic so some topics are held out; (2) train 1-3 epochs with a small learning rate and watch for memorisation; (3) test with *new* paraphrased questions and with the section-5 questions; (4) compare against the same base model plus RAG; keep whichever answers more accurately.
- **Before training, add:** more paraphrases per topic written by you, multi-turn follow-ups, and answers about the real repository once it has been inspected. The current data is a start, not a complete corpus.
- **Do not train on:** secrets, personal data, or claims that are not yet true (for example "NEXUS is implemented").

## 7. Maintenance
- Edit the facts in one place (the generator source), regenerate both files, and bump the date.
- When the repository is inspected or decisions D1-D10 are approved, replace **proposed** / **undecided** statements and regenerate.
