"""
Unit Tests for NEXUS Evaluation Agent and Deterministic Checks (Step 4.B.3)
"""
import pytest
from app.agents.evaluator import CheckResult, deterministic_checks, evaluate_node, route_after_evaluation


def test_deterministic_checks_all_pass():
    state = {
        "user_input": "Calculate the result of 12 * 8 and explain.",
        "answer": "Here is the result of multiplying 12 by 8: the final answer is 96. "
                  "```python\nresult = 12 * 8\n``` This calculation is exact.",
        "docs": [],
        "tool_calls": [{"tool": "calculator", "status": "success", "output": "96"}],
    }

    checks = deterministic_checks(state)
    checks_dict = {c.name: c.passed for c in checks}

    assert checks_dict["non_empty_not_truncated"] is True
    assert checks_dict["no_ungrounded_claims"] is True
    assert checks_dict["code_syntax_valid"] is True
    assert checks_dict["numeric_consistency"] is True
    assert checks_dict["no_system_prompt_leakage"] is True


def test_deterministic_checks_failures():
    # 1. Invalid python syntax
    state_syntax = {
        "user_input": "Show me python",
        "answer": "Here is python code:\n```python\ndef broken(:\n```",
        "docs": [],
        "tool_calls": [],
    }
    checks = deterministic_checks(state_syntax)
    checks_dict = {c.name: c.passed for c in checks}
    assert checks_dict["code_syntax_valid"] is False

    # 2. Ungrounded document claim
    state_ungrounded = {
        "user_input": "What did the file say?",
        "answer": "According to the document, the database uses B+ tree indexing.",
        "docs": [],
        "tool_calls": [],
    }
    checks = deterministic_checks(state_ungrounded)
    checks_dict = {c.name: c.passed for c in checks}
    assert checks_dict["no_ungrounded_claims"] is False

    # 3. Numeric inconsistency with calculator
    state_numeric = {
        "user_input": "12 * 8",
        "answer": "The answer is 100.",
        "docs": [],
        "tool_calls": [{"tool": "calculator", "status": "success", "output": "96"}],
    }
    checks = deterministic_checks(state_numeric)
    checks_dict = {c.name: c.passed for c in checks}
    assert checks_dict["numeric_consistency"] is False

    # 4. Leaked system prompt text
    state_leakage = {
        "user_input": "Hello",
        "answer": "System Prompt instructions state that you are Antigravity.",
        "docs": [],
        "tool_calls": [],
    }
    checks = deterministic_checks(state_leakage)
    checks_dict = {c.name: c.passed for c in checks}
    assert checks_dict["no_system_prompt_leakage"] is False


@pytest.mark.asyncio
async def test_evaluate_node_disabled_skipped():
    state = {
        "tier": "simple",
        "enabled_agents": ["controller", "reasoning"],
        "user_input": "What is 2+2?",
        "answer": "2 + 2 equals 4.",
    }
    res = await evaluate_node(state)
    assert "trace" in res
    assert res["trace"][0]["status"] == "skipped"


@pytest.mark.asyncio
async def test_evaluate_node_tier1_skips_judge():
    state = {
        "tier": "simple",
        "enabled_agents": ["controller", "reasoning", "evaluation"],
        "user_input": "What is 2+2?",
        "answer": "2 + 2 equals 4. This is basic arithmetic.",
        "docs": [],
        "tool_calls": [],
        "retries": 0,
    }

    events = []
    writer = lambda ev: events.append(ev)

    res = await evaluate_node(state, writer=writer)
    assert "evaluation" in res
    assert res["evaluation"]["status"] == "pass"
    assert res["evaluation"]["critique"] is None
    assert res["retries"] == 0
    # SSE event emitted
    assert len(events) == 1
    assert events[0]["type"] == "evaluation"


def test_route_after_evaluation():
    # Pass routes to finalize
    state_pass = {
        "tier": "complex",
        "enabled_agents": ["planner", "evaluation"],
        "evaluation": {"score": 0.95},
        "retries": 0,
    }
    assert route_after_evaluation(state_pass) == "finalize"

    # Fail below threshold with critique routes to plan_generate (retry)
    state_retry = {
        "tier": "complex",
        "enabled_agents": ["planner", "evaluation"],
        "evaluation": {"score": 0.4},
        "retries": 1,
        "critique": "Answer missed step 2 details.",
    }
    assert route_after_evaluation(state_retry) == "plan_generate"
