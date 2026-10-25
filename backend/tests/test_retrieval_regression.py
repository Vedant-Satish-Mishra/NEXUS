"""
Regression Test for Hybrid Retrieval (Step 4.C.1)
Verifies Hit@3 does not drop by more than 5 percentage points below stored baseline.
"""
import json
from pathlib import Path
import pytest
from app.rag.hybrid import HybridRetriever
from app.schemas.core import Principal

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.asyncio
async def test_retrieval_regression():
    baseline_path = PROJECT_ROOT / "data" / "eval" / "retrieval_baseline.json"
    golden_path = PROJECT_ROOT / "data" / "eval" / "golden.jsonl"

    assert baseline_path.exists(), "retrieval_baseline.json must exist"
    assert golden_path.exists(), "golden.jsonl must exist"

    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    baseline_hit_3 = baseline.get("hit_at_3", 0.95)

    questions = []
    with open(golden_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    # Test on a representative subset of answerable questions (first 10)
    answerable_subset = [q for q in questions if "none" not in q.get("expected_source", "").lower()][:10]
    assert len(answerable_subset) >= 5

    retriever = HybridRetriever()
    principal = Principal(user_id="test_reg", conversation_id="conv_reg")

    hits_3 = 0
    for q in answerable_subset:
        expected = q["expected_source"].strip().lower()
        results = await retriever.search_hybrid(
            principal=principal,
            query=q["question"],
            top_k=5,
            min_score=0.35,
        )
        for rank, r in enumerate(results[:3], start=1):
            file_name = r.get("file", "").strip().lower()
            if expected in file_name or file_name in expected:
                hits_3 += 1
                break

    subset_hit_3 = hits_3 / len(answerable_subset)

    # Fail CI if Hit@3 falls more than 5 points below baseline
    assert subset_hit_3 >= (baseline_hit_3 - 0.05), (
        f"Retrieval regression detected: Hit@3 ({subset_hit_3:.3f}) fell > 5 points below baseline ({baseline_hit_3:.3f})"
    )
