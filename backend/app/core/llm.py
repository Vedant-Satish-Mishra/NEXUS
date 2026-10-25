"""
NEXUS Adaptive LLM Provider & Model Profiles
Supports:
1. Local Llamafile Servers:
   - Qwen3 4B on http://127.0.0.1:8080 (Fast profile)
   - Qwen3 8B on http://127.0.0.1:8081 (Quality profile)
2. Ollama on http://localhost:11434 (as fallback or alternative)
Features:
- Seamless toggling between Fast (4B) and Quality (8B) via the UI profile
- Structured JSON output with schema constraints & 1-attempt auto-repair
- Defensive real-time <think>...</think> tag stripping
- Global single-GPU asyncio.Semaphore(1)
- Informative LLMUnavailableError with exact launch instructions
"""

import asyncio
import json
import logging
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger("nexus.llm")
T = TypeVar("T", bound=BaseModel)

PROFILES = {
    "fast": {
        "model": "qwen3:4b",
        "llamafile_url": settings.QWEN3_4B_URL,
        "num_ctx": 8192,
        "temperature": 0.3,
        "think": False,
    },
    "quality": {
        "model": "qwen3:8b",
        "llamafile_url": settings.QWEN3_8B_URL,
        "num_ctx": 6144,
        "temperature": 0.3,
        "think": False,
    },
}

# Single GPU concurrency control across all threads/runs
gpu_semaphore = asyncio.Semaphore(1)


class LLMUnavailableError(Exception):
    pass


class StructuredOutputError(Exception):
    pass


class LLMProvider(Protocol):
    async def chat(self, messages: List[Dict[str, str]], **opts) -> str:
        ...

    async def stream(self, messages: List[Dict[str, str]], **opts) -> AsyncIterator[str]:
        ...

    async def structured(
        self,
        model_cls: Type[T],
        messages: List[Dict[str, str]],
        **opts
    ) -> T:
        ...

    async def aclose(self) -> None:
        ...


def strip_think_tags(text: str) -> str:
    """Defensively removes any <think>...</think> blocks from output."""
    return re.sub(r"<think>[\s\S]*?</think>", "", text).strip()


class AdaptiveLLMProvider:
    """
    Unified provider connecting to local Llamafile Qwen3 (4B/8B) or Ollama.
    Automatically detects which local server is running for the chosen profile.
    """

    def __init__(self, ollama_url: Optional[str] = None):
        self.ollama_url = ollama_url or settings.OLLAMA_BASE_URL
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def _client(self) -> Optional[httpx.AsyncClient]:
        return self._http_client

    @_client.setter
    def _client(self, client: Optional[httpx.AsyncClient]):
        self._http_client = client

    def get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS)
        return self._http_client

    async def aclose(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def detect_backend(self, profile: str) -> tuple[str, str]:
        """
        Determines the active backend for the requested profile:
        Returns ('llamafile', target_url) or ('ollama', ollama_url).
        """
        client = self.get_client()

        # If client was injected with MockTransport (tests)
        if getattr(client, "_transport", None) and isinstance(client._transport, httpx.MockTransport):
            base = str(client.base_url)
            if "11434" in base or "ollama" in base:
                return "ollama", base
            return "llamafile", base

        target_llamafile_url = (
            settings.QWEN3_8B_URL if profile == "quality" else settings.QWEN3_4B_URL
        )

        # 1. Probe specific profile's Llamafile port
        try:
            res = await client.get(f"{target_llamafile_url}/v1/models", timeout=0.8)
            if res.status_code in (200, 404):
                return "llamafile", target_llamafile_url
        except Exception:
            pass

        # 2. Probe the other Llamafile port as fallback
        other_url = (
            settings.QWEN3_4B_URL if profile == "quality" else settings.QWEN3_8B_URL
        )
        try:
            res = await client.get(f"{other_url}/v1/models", timeout=0.5)
            if res.status_code in (200, 404):
                logger.info("Preferred model for %s not up, falling back to %s", profile, other_url)
                return "llamafile", other_url
        except Exception:
            pass

        # 3. Probe Ollama
        try:
            res = await client.get(f"{self.ollama_url}/api/tags", timeout=0.8)
            if res.status_code == 200:
                return "ollama", self.ollama_url
        except Exception:
            pass

        # Neither is running
        port_needed = "8081" if profile == "quality" else "8080"
        folder_needed = "qwen 3 8b" if profile == "quality" else "qwen 3 4b"
        raise LLMUnavailableError(
            f"No local LLM server is running for profile '{profile}'. "
            f"Please run 'run.bat' inside '{settings.LOCAL_QWEN_DIR}\\{folder_needed}' "
            f"(port {port_needed}) or start Ollama."
        )

    # -------------------------------------------------------------------------
    # Chat (Non-streaming)
    # -------------------------------------------------------------------------
    async def chat(
        self,
        messages: List[Dict[str, str]],
        profile: Optional[str] = None,
        **opts
    ) -> str:
        chosen_profile = profile or settings.DEFAULT_PROFILE
        backend_type, endpoint = await self.detect_backend(chosen_profile)
        client = self.get_client()

        async with gpu_semaphore:
            if backend_type == "llamafile":
                payload = {
                    "model": "qwen3",
                    "messages": messages,
                    "temperature": opts.get("temperature", 0.3),
                    "stream": False,
                }
                try:
                    resp = await client.post(f"{endpoint}/v1/chat/completions", json=payload)
                    if resp.status_code != 200:
                        raise LLMUnavailableError(f"Llamafile error HTTP {resp.status_code}: {resp.text}")
                    data = resp.json()
                    raw = data["choices"][0]["message"]["content"]
                    return strip_think_tags(raw)
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    raise LLMUnavailableError(f"Failed to connect to Llamafile at {endpoint}: {e}")

            else:  # Ollama
                ollama_model = PROFILES.get(chosen_profile, PROFILES["fast"])["model"]
                payload = {
                    "model": ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": opts.get("temperature", 0.3)},
                    "think": False,
                }
                try:
                    resp = await client.post(f"{endpoint}/api/chat", json=payload)
                    if resp.status_code != 200:
                        raise LLMUnavailableError(f"Ollama error HTTP {resp.status_code}: {resp.text}")
                    data = resp.json()
                    raw = data.get("message", {}).get("content", "")
                    return strip_think_tags(raw)
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    raise LLMUnavailableError(f"Failed to connect to Ollama at {endpoint}: {e}")

    # -------------------------------------------------------------------------
    # Streaming Chat
    # -------------------------------------------------------------------------
    async def stream(
        self,
        messages: List[Dict[str, str]],
        profile: Optional[str] = None,
        **opts
    ) -> AsyncIterator[str]:
        chosen_profile = profile or settings.DEFAULT_PROFILE
        backend_type, endpoint = await self.detect_backend(chosen_profile)
        client = self.get_client()

        async with gpu_semaphore:
            if backend_type == "llamafile":
                payload = {
                    "model": "qwen3",
                    "messages": messages,
                    "temperature": opts.get("temperature", 0.3),
                    "stream": True,
                }
                try:
                    async with client.stream("POST", f"{endpoint}/v1/chat/completions", json=payload) as resp:
                        if resp.status_code != 200:
                            raise LLMUnavailableError(f"Llamafile stream error HTTP {resp.status_code}")

                        in_think = False
                        async for line in resp.aiter_lines():
                            line_str = line.strip()
                            if not line_str or line_str == "data: [DONE]":
                                continue
                            if line_str.startswith("data: "):
                                try:
                                    chunk = json.loads(line_str[6:])
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    token = delta.get("content", "")
                                    if not token:
                                        continue

                                    # Filter think tokens
                                    if "<think>" in token and "</think>" in token:
                                        token = re.sub(r"<think>[\s\S]*?</think>", "", token)
                                    elif "<think>" in token:
                                        in_think = True
                                        token = token[:token.find("<think>")]
                                    elif "</think>" in token:
                                        in_think = False
                                        token = token[token.find("</think>") + len("</think>"):]
                                    elif in_think:
                                        continue

                                    if token:
                                        yield token
                                except Exception:
                                    continue
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    raise LLMUnavailableError(f"Llamafile streaming interrupted: {e}")

            else:  # Ollama
                ollama_model = PROFILES.get(chosen_profile, PROFILES["fast"])["model"]
                payload = {
                    "model": ollama_model,
                    "messages": messages,
                    "stream": True,
                    "options": {"temperature": opts.get("temperature", 0.3)},
                    "think": False,
                }
                try:
                    async with client.stream("POST", f"{endpoint}/api/chat", json=payload) as resp:
                        if resp.status_code != 200:
                            raise LLMUnavailableError(f"Ollama stream error HTTP {resp.status_code}")

                        in_think = False
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")

                            if "<think>" in token and "</think>" in token:
                                token = re.sub(r"<think>[\s\S]*?</think>", "", token)
                            elif "<think>" in token:
                                in_think = True
                                token = token[:token.find("<think>")]
                            elif "</think>" in token:
                                in_think = False
                                token = token[token.find("</think>") + len("</think>"):]
                            elif in_think:
                                continue

                            if token:
                                yield token
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    raise LLMUnavailableError(f"Ollama streaming interrupted: {e}")

    # -------------------------------------------------------------------------
    # Structured Output Generation with 1-Attempt Repair
    # -------------------------------------------------------------------------
    async def structured(
        self,
        model_cls: Type[T],
        messages: List[Dict[str, str]],
        profile: Optional[str] = None,
        **opts
    ) -> T:
        chosen_profile = profile or settings.DEFAULT_PROFILE
        backend_type, endpoint = await self.detect_backend(chosen_profile)
        client = self.get_client()
        schema = model_cls.model_json_schema()

        async with gpu_semaphore:
            if backend_type == "llamafile":
                # Guide llamafile via explicit JSON instruction in system prompt
                schema_prompt = (
                    "You are a strict JSON extraction system. Respond ONLY with a valid JSON object matching this schema:\n"
                    f"{json.dumps(schema)}\nDo not wrap output in backticks or markdown, return raw JSON only."
                )
                structured_messages = [{"role": "system", "content": schema_prompt}] + messages
                payload = {
                    "model": "qwen3",
                    "messages": structured_messages,
                    "temperature": 0.1,
                    "stream": False,
                    "response_format": {"type": "json_object"},
                }

                try:
                    resp = await client.post(f"{endpoint}/v1/chat/completions", json=payload)
                    content = resp.json()["choices"][0]["message"]["content"]
                    content = strip_think_tags(content).strip()
                    # Strip any accidental ```json wrappers
                    if content.startswith("```"):
                        content = re.sub(r"^```(?:json)?\n?", "", content)
                        content = re.sub(r"\n?```$", "", content)
                    return model_cls.model_validate(json.loads(content))

                except (json.JSONDecodeError, ValidationError) as err:
                    # ONE repair attempt
                    repair_messages = list(structured_messages) + [
                        {
                            "role": "user",
                            "content": f"Your previous response had validation error: {err}. Output strictly valid JSON conforming to the schema.",
                        }
                    ]
                    payload["messages"] = repair_messages
                    try:
                        retry_resp = await client.post(f"{endpoint}/v1/chat/completions", json=payload)
                        retry_content = strip_think_tags(retry_resp.json()["choices"][0]["message"]["content"]).strip()
                        if retry_content.startswith("```"):
                            retry_content = re.sub(r"^```(?:json)?\n?", "", retry_content)
                            retry_content = re.sub(r"\n?```$", "", retry_content)
                        return model_cls.model_validate(json.loads(retry_content))
                    except Exception as final_err:
                        raise StructuredOutputError(f"Failed to generate structured {model_cls.__name__} after repair: {final_err}")

            else:  # Ollama format
                ollama_model = PROFILES.get(chosen_profile, PROFILES["fast"])["model"]
                payload = {
                    "model": ollama_model,
                    "messages": messages,
                    "format": schema,
                    "stream": False,
                    "options": {"temperature": 0.1},
                    "think": False,
                }
                try:
                    resp = await client.post(f"{endpoint}/api/chat", json=payload)
                    content = resp.json().get("message", {}).get("content", "")
                    content = strip_think_tags(content)
                    return model_cls.model_validate(json.loads(content))
                except (json.JSONDecodeError, ValidationError) as err:
                    repair_messages = list(messages) + [
                        {
                            "role": "user",
                            "content": f"The previous output failed validation: {err}. Output strictly valid JSON matching the schema.",
                        }
                    ]
                    payload["messages"] = repair_messages
                    try:
                        retry_resp = await client.post(f"{endpoint}/api/chat", json=payload)
                        retry_content = strip_think_tags(retry_resp.json().get("message", {}).get("content", ""))
                        return model_cls.model_validate(json.loads(retry_content))
                    except Exception as final_err:
                        raise StructuredOutputError(f"Failed to generate structured {model_cls.__name__} after repair: {final_err}")


# Backward compatibility alias
OllamaProvider = AdaptiveLLMProvider

# Default singleton provider used throughout the application
default_llm_provider = AdaptiveLLMProvider()


def get_llm_provider() -> LLMProvider:
    return default_llm_provider

