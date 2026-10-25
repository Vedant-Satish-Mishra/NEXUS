"""
NEXUS Reasoning Agent
Step 2.B.4 & Milestone 4 — Grounded reasoning, tool execution grounding, critique incorporation, and streaming
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional
from langgraph.types import StreamWriter

from app.agents.registry import guarded, traced
from app.core.llm import LLMProvider, default_llm_provider, get_llm_provider
from app.schemas.events import CitationItem

logger = logging.getLogger("nexus.agents.reasoning")


def build_reasoning_prompt(
    user_input: str,
    history: List[Dict[str, str]],
    docs: List[Dict[str, Any]],
    plan: Optional[Dict[str, Any]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
    understanding: Optional[Dict[str, Any]] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    critique: Optional[str] = None,
    max_context_chars: int = 24000
) -> List[Dict[str, str]]:
    """
    Constructs the prompt within strict context budgets.
    Structure:
    1. System instructions (grounding rules, citation syntax [S1], [S2])
    2. Context / Memories (if available)
    3. Approved Plan (if available)
    4. Tool Execution Results (if available)
    5. Critique from previous evaluation attempt (if available)
    6. Grounding Sources ([S1], [S2] ... [S6])
    7. Prior conversation turns
    8. Current user input
    """
    system_parts = [
        "You are NEXUS, a rigorous, local-first cognitive AI assistant.",
        "Your answers must be clear, accurate, and directly helpful.",
    ]

    if docs:
        system_parts.extend([
            "GROUNDING RULES:",
            "- Ground your answer in the numbered SOURCES provided below.",
            "- When referencing facts from a source, cite it inline using bracketed tags: [S1], [S2], etc.",
            "- If the provided sources do not contain the answer, explicitly state: 'My knowledge base does not cover this topic.' Do not fabricate facts."
        ])
    else:
        system_parts.append("Answer clearly and concisely using your best knowledge.")

    system_instruction = "\n".join(system_parts)

    # 1. System Message
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_instruction}]

    # 2. Context / Plan / Sources / Tools Block
    context_blocks = []
    if memories:
        mem_str = "\n".join([f"- {m.get('content')}" for m in memories[:5]])
        context_blocks.append(f"RECALLED USER MEMORIES:\n{mem_str}")

    if plan and plan.get("steps"):
        plan_str = f"APPROVED EXECUTION PLAN (Goal: {plan.get('goal')}):\n"
        for idx, step in enumerate(plan.get("steps", [])):
            plan_str += f"{idx+1}. {step.get('title')}: {step.get('detail')}\n"
        context_blocks.append(plan_str)

    if tool_calls:
        tc_lines = ["TOOL EXECUTION RESULTS (Untrusted Data):"]
        for tc in tool_calls:
            status_text = tc.get("status", "completed")
            tc_lines.append(
                f"- Tool [{tc.get('tool')}] Status: {status_text}\n"
                f"  Input: {tc.get('input')}\n"
                f"  Output: {tc.get('output')}"
            )
        context_blocks.append("\n".join(tc_lines))

    if critique:
        context_blocks.append(
            f"PREVIOUS ATTEMPT EVALUATION CRITIQUE:\n{critique}\nPlease address this critique in your updated response."
        )

    if docs:
        source_str = "NUMBERED SOURCES FOR GROUNDING:\n"
        for idx, doc in enumerate(docs[:6]):
            tag = f"[S{idx+1}]"
            src = doc.get("source", "knowledge_base")
            pg = doc.get("page", 1)
            topic = doc.get("topic", "")
            text = doc.get("text", "")
            # Budget chunk text to ~1000 chars each
            truncated_text = text[:1200]
            source_str += f"\n--- SOURCE {tag} (File: {src}, Topic: {topic}, Page: {pg}) ---\n{truncated_text}\n"
        context_blocks.append(source_str)

    if context_blocks:
        messages.append({
            "role": "user",
            "content": "[BACKGROUND CONTEXT & GROUNDING MATERIALS]\n" + "\n\n".join(context_blocks)
        })
        messages.append({
            "role": "assistant",
            "content": "Acknowledged. I will strictly reference these materials and use [S#] citations where applicable."
        })

    # 3. Conversation History
    for turn in history[-4:]:
        messages.append({
            "role": turn.get("role", "user"),
            "content": turn.get("content", "")
        })

    # 4. Final User Question
    messages.append({
        "role": "user",
        "content": user_input
    })

    return messages


def extract_citations(answer: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts inline [S1], [S2] tags from the answer and matches them to docs.
    """
    if not docs:
        return []

    tags = set(re.findall(r'\[S(\d+)\]', answer))
    citations: List[Dict[str, Any]] = []

    for tag in sorted(tags):
        idx = int(tag) - 1
        if 0 <= idx < len(docs):
            d = docs[idx]
            citations.append({
                "file": d.get("source", "unknown"),
                "page": d.get("page", 1),
                "score": d.get("score", 0.0),
                "chunk_id": d.get("id", ""),
                "snippet": d.get("text", "")[:200]
            })

    return citations


def create_reasoning_node(llm_provider: Optional[LLMProvider] = None):
    llm = llm_provider or default_llm_provider

    @guarded("reasoning")
    @traced("reason")
    async def reasoning_node(state: Dict[str, Any], writer: StreamWriter) -> Dict[str, Any]:
        t0 = time.perf_counter()
        user_input = state.get("user_input", "")
        history = state.get("history", [])
        docs = state.get("docs", [])
        plan = state.get("plan")
        memories = state.get("memories", [])
        understanding = state.get("understanding")
        tool_calls = state.get("tool_calls", [])
        critique = state.get("critique")
        profile = state.get("profile", "fast")

        # Emit sources event if docs present and writer available
        if docs and writer:
            sources_event = {
                "type": "sources",
                "sources": [
                    {
                        "file": d.get("source", "knowledge_base"),
                        "page": d.get("page", 1),
                        "score": d.get("score", 0.0),
                        "chunk_id": d.get("id", ""),
                        "snippet": d.get("text", "")[:160]
                    }
                    for d in docs
                ]
            }
            writer(sources_event)

        messages = build_reasoning_prompt(
            user_input=user_input,
            history=history,
            docs=docs,
            plan=plan,
            memories=memories,
            understanding=understanding,
            tool_calls=tool_calls,
            critique=critique,
        )

        tokens: List[str] = []
        try:
            async for token in llm.stream(messages, profile=profile):
                tokens.append(token)
                if writer:
                    writer({"type": "token", "content": token})
        except Exception as exc:
            ms = int((time.perf_counter() - t0) * 1000)
            logger.error(f"Reasoning node stream error: {exc}", exc_info=True)
            return {
                "answer": "".join(tokens),
                "trace": [{
                    "node": "reason",
                    "status": "error",
                    "ms": ms,
                    "summary": f"Reasoning stream failed: {exc}"
                }]
            }

        full_answer = "".join(tokens)
        ms = int((time.perf_counter() - t0) * 1000)
        citations = extract_citations(full_answer, docs)

        return {
            "answer": full_answer,
            "citations": citations,
            "trace": [{
                "node": "reason",
                "status": "ok",
                "ms": ms,
                "summary": f"Generated grounded response ({len(full_answer)} chars, {len(citations)} citations) in {ms}ms"
            }]
        }

    return reasoning_node
