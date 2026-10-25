# NEXUS Evaluation Golden Question Set (`data/eval/README.md`)

This directory houses the benchmark dataset (`data/eval/golden.jsonl`) used to validate retrieval quality, answer correctness, plan generation, and security guardrails across development milestones.

## 1. Composition of the 40-Question Golden Set

The 40 questions are systematically categorized into:
- **10 Simple Factual Queries (Tier 1):** Single-hop definitions (e.g. `What is a HashMap in Java?`). Evaluates baseline LLM accuracy and latency without RAG.
- **15 Document-Grounded Queries (Tier 2):** Questions requiring evidence from `data/knowledge/` (e.g. `Summarize the sliding window pattern...`). Evaluates hybrid retrieval hit@k and citation fidelity.
- **10 Planning / Complex Queries (Tier 3):** Decomposable, multi-week preparation requests (e.g. `Create a 4-month preparation plan...`). Evaluates Understanding extraction, Plan step topological ordering, and Evaluation agent score.
- **5 Adversarial Queries:** Unanswerable, medical, financial, or prompt-injection attempts (questions 36–40). Evaluates refusal-to-guess behavior and system safety.

## 2. Evaluation Metrics Computed

In Steps 4.C.1 and 5.B.2 (`scripts/eval_retrieval.py` and `scripts/eval_ablation.py`), the following metrics are computed against this set:
1. **Retrieval Hit@k (k=1, 3, 5):** Proportion of document-grounded questions where `expected_source` appears in the top $k$ retrieved chunks.
2. **Mean Reciprocal Rank (MRR):** Reciprocal rank of the first relevant chunk.
3. **Key-Point Coverage:** Automated keyword/phrase match of the response against `expected_points`.
4. **Uncertainty / Refusal Rate:** True Positive rate on the 5 adversarial questions (refusing rather than hallucinating).
5. **Latency p50 & p95:** Execution time breakdown per routing tier.
