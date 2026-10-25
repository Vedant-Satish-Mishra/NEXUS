"""
NEXUS Evaluation Agent & Bounded Auto-Replan Loop
Step 4.B.3 — Evaluation Agent and bounded retry
"""
import ast
import json
import logging
import re
from typing import Any, Dict, List, Optional
from langgraph.types import StreamWriter
from pydantic import BaseModel, Field

from app.agents.registry import guarded, traced
from app.core.config import settings
from app.core.llm import LLMProvider, default_llm_provider

logger = logging.getLogger("nexus.agents.evaluator")


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str = ""
    weight: float = 1.0


class LLMJudgeOutput(BaseModel):
    groundedness: float = Field(..., ge=0.0, le=1.0, description="Score 0.0-1.0 grounded in evidence")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Score 0.0-1.0 directly answers user prompt")
    completeness: float = Field(..., ge=0.0, le=1.0, description="Score 0.0-1.0 all sub-questions addressed")
    critique: str = Field(..., max_length=500, description="Actionable critique in 1-3 sentences")


def deterministic_checks(state: Dict[str, Any]) -> List[CheckResult]:
    """Runs deterministic, rule-based verification checks over the generated answer."""
    checks: List[CheckResult] = []
    answer = state.get("answer", "").strip()
    docs = state.get("docs", [])
    user_input = state.get("user_input", "")

    # 1. Non-empty and not truncated
    is_non_empty = len(answer) > 20
    is_not_truncated = not (answer.endswith("...") or answer.count("```") % 2 != 0)
    checks.append(
        CheckResult(
            name="non_empty_not_truncated",
            passed=is_non_empty and is_not_truncated,
            detail="Answer is complete and properly formatted without abrupt cutoff."
            if (is_non_empty and is_not_truncated)
            else "Answer is too short or cut off mid-sentence.",
            weight=1.5,
        )
    )

    # 2. Citation markers refer to real evidence
    citations = re.findall(r"\[(?:S(\d+)|(\d+))\]", answer)
    if citations:
        max_doc_idx = len(docs)
        citations_valid = True
        for s_idx, d_idx in citations:
            idx = int(s_idx if s_idx else d_idx)
            if idx < 1 or idx > max_doc_idx:
                citations_valid = False
                break
        checks.append(
            CheckResult(
                name="citations_valid",
                passed=citations_valid,
                detail="Citations accurately reference available source documents."
                if citations_valid
                else "Answer contains invalid citation references not found in sources.",
                weight=1.2,
            )
        )

    # 3. No ungrounded claims of document evidence
    claims_doc = bool(
        re.search(
            r"\b(according to the document|as stated in the file|the uploaded notes state)\b",
            answer,
            re.IGNORECASE,
        )
    )
    if not docs and claims_doc:
        checks.append(
            CheckResult(
                name="no_ungrounded_claims",
                passed=False,
                detail="Answer claims document evidence but no documents were retrieved.",
                weight=1.5,
            )
        )
    else:
        checks.append(
            CheckResult(
                name="no_ungrounded_claims",
                passed=True,
                detail="No false claims of document grounding.",
                weight=1.0,
            )
        )

    # 4. Plan / requirement coverage
    plan = state.get("plan", {})
    steps = plan.get("steps", [])
    if steps:
        matched_steps = 0
        for step in steps:
            desc = step.get("description", "").lower()
            words = [w for w in re.findall(r"\w+", desc) if len(w) > 3]
            if any(w in answer.lower() for w in words):
                matched_steps += 1
        coverage = matched_steps / len(steps) if steps else 1.0
        checks.append(
            CheckResult(
                name="plan_coverage",
                passed=coverage >= 0.5,
                detail=f"Plan requirement coverage: {coverage:.1%}.",
                weight=1.2,
            )
        )

    # 5. Code syntax validation (Python ast.parse, JSON loads)
    py_blocks = re.findall(r"```python\s*(.*?)\s*```", answer, re.DOTALL)
    py_syntax_ok = True
    for code in py_blocks:
        try:
            ast.parse(code)
        except Exception:
            py_syntax_ok = False
            break

    json_blocks = re.findall(r"```json\s*(.*?)\s*```", answer, re.DOTALL)
    json_syntax_ok = True
    for code in json_blocks:
        try:
            json.loads(code)
        except Exception:
            json_syntax_ok = False
            break

    checks.append(
        CheckResult(
            name="code_syntax_valid",
            passed=py_syntax_ok and json_syntax_ok,
            detail="All extracted code blocks have valid syntax."
            if (py_syntax_ok and json_syntax_ok)
            else "Code blocks have syntax errors.",
            weight=1.0,
        )
    )

    # 6. Numeric consistency with calculator tools
    tool_calls = state.get("tool_calls", [])
    calc_consistent = True
    for tc in tool_calls:
        if tc.get("tool") == "calculator" and tc.get("status") in ("success", "ok"):
            calc_out = str(tc.get("output", "")).strip()
            if calc_out and calc_out not in answer:
                calc_consistent = False
                break
    checks.append(
        CheckResult(
            name="numeric_consistency",
            passed=calc_consistent,
            detail="Numeric results consistent with calculator execution.",
            weight=1.0,
        )
    )

    # 7. No internal system-prompt leakage
    leakage = bool(
        re.search(
            r"\b(System Prompt|You are Antigravity|You are NEXUS|CogState|Pydantic schema)\b",
            answer,
            re.IGNORECASE,
        )
    )
    checks.append(
        CheckResult(
            name="no_system_prompt_leakage",
            passed=not leakage,
            detail="Clean answer without prompt instruction leakage."
            if not leakage
            else "Detected leaked system instructions.",
            weight=2.0,
        )
    )

    return checks


@guarded("evaluation")
@traced("evaluate")
async def evaluate_node(
    state: Dict[str, Any],
    writer: StreamWriter,
    llm: Optional[LLMProvider] = None,
) -> Dict[str, Any]:
    """
    Evaluates the response:
    - Runs deterministic checks always.
    - Runs LLM judge pass only for Tier 3 (complex) when 'evaluation' agent is enabled.
    - Decides whether to auto re-plan/retry if score is below threshold.
    """
    checks = deterministic_checks(state)
    checks_map = {c.name: c.passed for c in checks}

    # Deterministic score
    total_weight = sum(c.weight for c in checks)
    passed_weight = sum(c.weight for c in checks if c.passed)
    rule_score = passed_weight / total_weight if total_weight > 0 else 1.0

    tier = state.get("tier", "simple")
    enabled = state.get("enabled_agents", [])
    critique = None
    final_score = rule_score

    # LLM Judge pass: Tier 3 only and evaluation enabled
    if tier == "complex" and "evaluation" in enabled:
        provider = llm or default_llm_provider
        try:
            judge_prompt = (
                f"Evaluate the assistant's answer.\n\n"
                f"User Question:\n{state.get('user_input', '')}\n\n"
                f"Retrieved Documents:\n{json.dumps([d.get('snippet', '') for d in state.get('docs', [])])}\n\n"
                f"Assistant Answer:\n{state.get('answer', '')}\n\n"
                f"Score groundedness (0-1), relevance (0-1), completeness (0-1), and critique in 1-3 sentences."
            )
            judge_res: LLMJudgeOutput = await provider.structured(
                schema=LLMJudgeOutput,
                prompt=judge_prompt,
                system="You are a strict evaluation judge. Grade rigorously on evidence grounding and question coverage.",
            )
            judge_score = (judge_res.groundedness * 0.4 + judge_res.relevance * 0.3 + judge_res.completeness * 0.3)
            critique = judge_res.critique
            final_score = (rule_score * 0.4) + (judge_score * 0.6)
        except Exception as e:
            logger.warning(f"LLM judge failed open: {e}")
            final_score = rule_score

    eval_threshold = getattr(settings, "EVAL_THRESHOLD", 0.7)
    max_retries = min(getattr(settings, "MAX_RETRIES", 1), 2)
    retries = state.get("retries", 0)

    # Retry condition (Tier 3 only)
    need_retry = (
        tier == "complex"
        and "evaluation" in enabled
        and final_score < eval_threshold
        and retries < max_retries
    )

    # Emit SSE Evaluation event
    if writer:
        writer(
            {
                "type": "evaluation",
                "score": round(final_score, 3),
                "checks": checks_map,
                "retry": need_retry,
                "critique": critique,
            }
        )

    eval_data = {
        "score": round(final_score, 3),
        "checks": checks_map,
        "critique": critique,
        "status": "fail" if final_score < eval_threshold else "pass",
    }

    return {
        "evaluation": eval_data,
        "retries": retries + 1 if need_retry else retries,
        "critique": critique if need_retry else None,
        "low_confidence": (final_score < eval_threshold and not need_retry),
    }


def route_after_evaluation(state: Dict[str, Any]) -> str:
    """Routes back to planning/reasoning if retry triggered, otherwise finalizes."""
    eval_res = state.get("evaluation", {})
    retries = state.get("retries", 0)
    max_retries = min(getattr(settings, "MAX_RETRIES", 1), 2)
    score = eval_res.get("score", 1.0)
    tier = state.get("tier", "simple")
    enabled = state.get("enabled_agents", [])

    if (
        tier == "complex"
        and "evaluation" in enabled
        and score < getattr(settings, "EVAL_THRESHOLD", 0.7)
        and retries <= max_retries
        and state.get("critique")
    ):
        # Auto-replan retry loop
        if "planner" in enabled:
            return "plan_generate"
        return "reason"

    return "finalize"
