"""
Unit Tests: LLM Provider, Profiles & Structured Output (Step 1.B.1)
Covers mock transport, think-tag stripping, repair loops, and error mapping.
"""
import json
import pytest
import httpx
from pydantic import BaseModel
from app.core.llm import (
    OllamaProvider,
    strip_think_tags,
    LLMUnavailableError,
    StructuredOutputError
)


class MockItem(BaseModel):
    name: str
    score: int


def test_strip_think_tags():
    raw = "<think>Internal deliberation...</think>Final grounded answer."
    assert strip_think_tags(raw) == "Final grounded answer."

    nested = "<think>first</think>Part 1<think>second</think>Part 2"
    assert strip_think_tags(nested) == "Part 1Part 2"


@pytest.mark.asyncio
async def test_ollama_chat_success():
    def handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={"message": {"content": "<think>Deliberating</think>JVM executes bytecode."}}
        )

    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://localhost:11434", transport=httpx.MockTransport(handler))

    answer = await provider.chat([{"role": "user", "content": "What is JVM?"}], profile="fast")
    assert answer == "JVM executes bytecode."
    await provider.aclose()


@pytest.mark.asyncio
async def test_ollama_stream_success():
    lines = [
        json.dumps({"message": {"content": "Hello "}}),
        json.dumps({"message": {"content": "<think>Skip</think>"}}),
        json.dumps({"message": {"content": "World!"}})
    ]
    stream_content = "\n".join(lines) + "\n"

    def handler(request: httpx.Request):
        return httpx.Response(200, content=stream_content.encode("utf-8"))

    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://localhost:11434", transport=httpx.MockTransport(handler))

    tokens = []
    async for tok in provider.stream([{"role": "user", "content": "Hi"}]):
        tokens.append(tok)

    assert "".join(tokens) == "Hello World!"
    await provider.aclose()


@pytest.mark.asyncio
async def test_ollama_structured_success_first_attempt():
    def handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={"message": {"content": json.dumps({"name": "Core Java", "score": 95})}}
        )

    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://localhost:11434", transport=httpx.MockTransport(handler))

    item = await provider.structured(MockItem, [{"role": "user", "content": "Score Java"}])
    assert item.name == "Core Java"
    assert item.score == 95
    await provider.aclose()


@pytest.mark.asyncio
async def test_ollama_structured_repair_attempt():
    attempt_count = 0

    def handler(request: httpx.Request):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            # First attempt returns invalid schema (missing score)
            return httpx.Response(200, json={"message": {"content": '{"name": "Invalid"}'}})
        # Second attempt returns repaired schema
        return httpx.Response(200, json={"message": {"content": '{"name": "Repaired", "score": 100}'}})

    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://localhost:11434", transport=httpx.MockTransport(handler))

    item = await provider.structured(MockItem, [{"role": "user", "content": "Give item"}])
    assert item.name == "Repaired"
    assert item.score == 100
    assert attempt_count == 2
    await provider.aclose()


@pytest.mark.asyncio
async def test_ollama_unreachable_error():
    def handler(request: httpx.Request):
        raise httpx.ConnectError("Connection refused by Ollama host", request=request)

    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://localhost:11434", transport=httpx.MockTransport(handler))

    with pytest.raises(LLMUnavailableError):
        await provider.chat([{"role": "user", "content": "Test"}])
    await provider.aclose()


@pytest.mark.asyncio
async def test_llamafile_openai_stream_and_think_tag_stripping():
    """Verify that OpenAI-compatible streaming from Llamafile strips think tags and streams answer."""
    stream_lines = [
        'data: {"choices":[{"delta":{"content":"<think>Internal thought</think>Direct"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":" answer from Qwen3"}}]}\n\n',
        'data: [DONE]\n\n'
    ]
    stream_content = "".join(stream_lines)

    def handler(request: httpx.Request):
        return httpx.Response(200, content=stream_content.encode("utf-8"))

    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://127.0.0.1:8080", transport=httpx.MockTransport(handler))

    tokens = []
    async for tok in provider.stream([{"role": "user", "content": "Hello"}], profile="fast"):
        tokens.append(tok)

    assert "".join(tokens) == "Direct answer from Qwen3"
    await provider.aclose()
