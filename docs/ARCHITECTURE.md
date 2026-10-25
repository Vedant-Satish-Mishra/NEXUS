# NEXUS Architecture: Seminar Mapping & System Mechanics (Step 5.D.3)

This document formalizes the mapping between the theoretical seminar concepts and the concrete implementation of the NEXUS cognitive system, detailing components, routing tiers, and honest deviations.

---

## 1. Seminar Component Mapping

| Seminar Concept | Theoretical Technique | NEXUS Implementation | Notes & Honest Deviations |
|---|---|---|---|
| **Query Understanding** | NLP + Transformer/LLM | `app.agents.understanding` (`Understanding` Pydantic model) | Structured extraction via Qwen3 with JSON schema constraint. Fast heuristic fallback for trivial queries. |
| **Executive Controller** | Decision Tree / Orchestrator | `app.agents.controller` (Deterministic Rule Router) | Hand-crafted deterministic rules matching requirements to tiers (Tier 1 Simple, Tier 2 Document, Tier 3 Complex). No LLM overhead. |
| **Knowledge Retrieval** | BM25 + TF-IDF | `app.rag.hybrid` (`rank_bm25` BM25Okapi) | BM25 is used as the probabilistic TF-IDF ranking function over candidate tokens. |
| **Semantic Retrieval** | Embedding + Cosine similarity | `app.rag.embeddings` (`FastEmbedEmbedder` + BGE-small) | 384-dimensional ONNX embeddings computed locally without touching GPU VRAM. |
| **Vector Search Index** | FAISS / HNSW | ChromaDB `PersistentClient` (Cosine HNSW) | Chroma's embedded HNSW engine is used for persistence and multi-collection partitioning. |
| **Memory Management** | Embedding + Recency/Importance | `app.agents.memory_agent` + `app.services.memory` | Recency decay ($T_{1/2} = 60\text{ days}$) and importance weighting. **Strict human consent invariant**: memories only saved upon explicit user confirmation. |
| **Planning & Graph Search** | A* / Graph Search | `app.agents.planner` (Topological Dependency Sort) | LLM generates structured 3-7 step plan; Kahn's algorithm validates acyclic dependencies and computes parallel execution paths. |
| **Reasoning Agent** | Multi-step Reasoning + Grounding | `app.agents.reasoning` (Context Budgeting + Citations) | Context budgeted strictly (8192 tokens for 4B, 6144 for 8B). Numbered citations `[S1]...[S6]` verified against evidence chunks. |
| **Evaluation Agent** | Self-Reflection & Rule Rubrics | `app.agents.evaluator` (Deterministic Rubrics + Judge) | 7 deterministic checks (citations, coverage, AST syntax, numeric consistency) + LLM judge in Tier 3. Bounded retry loop (max 1-2 replans). |
| **Tool Execution** | Code Execution & Tools | `app.tools` + `sandbox/` (Isolated Docker Service) | AST safe calculator (forbids imports/exponent bombs), scoped file reader, and sandboxed Python with **mandatory user approval modal**. |
| **Adaptive Learning** | Feedback-based Scoring | `app.services.learning` (`learning_signals` table) | Aggregates feedback with exponential decay. Threshold of $\ge 5$ samples. Adjusts strategy hints and retrieval source boosts ($\pm 10\%$). Never alters facts or fine-tunes weights. |

---

## 2. Dynamic Routing Tiers

1. **Tier 1 (Simple Q&A):**
   - Heuristics: Single question, no document references, no complex tasks.
   - Flow: `Controller -> Reasoning -> Finalize`.
   - Budget: 1 LLM call, ~400ms latency.

2. **Tier 2 (Document Grounded):**
   - Heuristics: Knowledge search, uploaded document summarization, technical references.
   - Flow: `Understanding -> Controller -> Context Gather -> Retrieval -> Grounded Reasoning -> Finalize`.
   - Budget: 2 LLM calls, ~1200ms latency.

3. **Tier 3 (Complex Synthesis):**
   - Heuristics: Multi-step plans, comparative analysis, coding tasks, calculations.
   - Flow: `Understanding -> Controller -> Context Gather -> Planner -> [USER APPROVAL] -> Retrieval -> Execute (Tools) -> Reasoning -> Evaluator -> (Bounded Auto-Replan if needed) -> Finalize`.
   - Budget: 4-5 LLM calls, interactive checkpoints.
