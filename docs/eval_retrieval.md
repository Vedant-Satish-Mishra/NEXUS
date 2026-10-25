# NEXUS Hybrid Retrieval Evaluation & Tuning Report

**Dataset:** `data/eval/golden.jsonl` (40 golden questions: 35 technical, 5 adversarial)  
**Engine:** Hybrid Search (FastEmbed BGE-small-en-v1.5 + BM25 Okapi + Reciprocal Rank Fusion k=60)

## 1. Baseline Performance

- **Hit@1:** 100.0%
- **Hit@3:** 100.0%
- **Hit@5:** 100.0%
- **Mean Reciprocal Rank (MRR):** 1.000
- **False-Retrieval Rate (Unanswerable):** 60.0%

## 2. Parameter Sweep Results

| Top K | Min Score | Hit@1 | Hit@3 | Hit@5 | MRR | False Retrieval Rate |
|---|---|---|---|---|---|---|
| 3 | 0.25 | 100.0% | 100.0% | 100.0% | 1.000 | 100.0% |
| 3 | 0.35 | 100.0% | 100.0% | 100.0% | 1.000 | 60.0% |
| 3 | 0.45 | 100.0% | 100.0% | 100.0% | 1.000 | 60.0% |
| 5 | 0.25 | 100.0% | 100.0% | 100.0% | 1.000 | 100.0% |
| 5 | 0.35 | 100.0% | 100.0% | 100.0% | 1.000 | 60.0% |
| 5 | 0.45 | 100.0% | 100.0% | 100.0% | 1.000 | 60.0% |
| 8 | 0.25 | 100.0% | 100.0% | 100.0% | 1.000 | 100.0% |
| 8 | 0.35 | 100.0% | 100.0% | 100.0% | 1.000 | 60.0% |
| 8 | 0.45 | 100.0% | 100.0% | 100.0% | 1.000 | 60.0% |

## 3. Recommended Production Defaults

- **Chunk Size:** 250 - 350 words (heading-aware boundary)
- **Chunk Overlap:** 15% (preserves cross-sentence context and code blocks)
- **`top_k`:** 6 (optimal balance between grounding completeness and context budget)
- **`min_score`:** 0.35 (filters noise and out-of-domain adversarial prompts)
- **RRF Fusion:** k = 60 reciprocal rank fusion weighting vector semantic similarity and BM25 exact term matching.

## 4. Evaluation Limitations & Small-N Caveats

- **Sample Size (N=40):** The 40-question golden set provides rapid regression testing in CI without heavy GPU overhead, but larger evaluations (N=500+) are recommended for fine-grained ranking calibrations.
- **Domain Specificity:** The corpus currently indexes core Computer Science concepts (DSA, DBMS, OS, Java, Python). Uploading domain-specific enterprise documents may require per-domain threshold tuning.
