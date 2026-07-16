"""
UnitForge — Pluggable LLM Client
=================================
Supports three providers:
  - claude  → Anthropic API (best quality, paid)
  - openai  → OpenAI API (alternative, paid)
  - ollama  → Local Ollama (completely free, no API key needed)

Usage:
    client = LLMClient.from_env()
    response = client.generate(prompt="Generate a unit test for...")

Configuration via environment variables (see .env.example):
    LLM_PROVIDER=ollama          # claude | openai | ollama
    ANTHROPIC_API_KEY=...        # only for claude
    OPENAI_API_KEY=...           # only for openai
    OLLAMA_BASE_URL=...          # only for ollama (default: http://localhost:11434)
    OLLAMA_MODEL=...             # only for ollama (default: deepseek-coder-v2)
"""

import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Response dataclass — same shape regardless of provider
# ─────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


# ─────────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────────

class BaseLLMProvider(ABC):
    """All providers implement this interface."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Send a prompt and return an LLMResponse."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...


# ─────────────────────────────────────────────────────────────
# Claude provider (Anthropic API)
# ─────────────────────────────────────────────────────────────

class ClaudeProvider(BaseLLMProvider):
    """
    Uses Anthropic SDK.
    Requires: ANTHROPIC_API_KEY in environment.
    Best quality for test generation.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        logger.info(f"ClaudeProvider initialised with model={self._model}")

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self._client.messages.create(**kwargs)
        content = response.content[0].text

        return LLMResponse(
            content=content,
            provider="claude",
            model=self._model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def provider_name(self) -> str:
        return "claude"


# ─────────────────────────────────────────────────────────────
# OpenAI provider
# ─────────────────────────────────────────────────────────────

class OpenAIProvider(BaseLLMProvider):
    """
    Uses OpenAI SDK.
    Requires: OPENAI_API_KEY in environment.
    """

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )
        self._client = OpenAI(api_key=api_key)
        self._model = model
        logger.info(f"OpenAIProvider initialised with model={self._model}")

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=4096,
        )
        content = response.choices[0].message.content

        return LLMResponse(
            content=content,
            provider="openai",
            model=self._model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

    def provider_name(self) -> str:
        return "openai"


# ─────────────────────────────────────────────────────────────
# Ollama provider (FREE — runs locally)
# ─────────────────────────────────────────────────────────────

class OllamaProvider(BaseLLMProvider):
    """
    Uses Ollama REST API (local).
    Completely FREE — no API key, no data leaves your machine.

    Install Ollama:  https://ollama.com
    Pull a model:    ollama pull deepseek-coder-v2

    Recommended models (best → lightest):
        deepseek-coder-v2   needs ~16GB RAM  (best quality)
        qwen2.5-coder:14b   needs ~10GB RAM  (great quality)
        codellama:13b        needs ~8GB RAM   (good for Python)
        qwen2.5-coder:7b    needs ~6GB RAM   (lightweight)
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "deepseek-coder-v2"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
    ) -> None:
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests package not installed. Run: pip install requests"
            )
        import requests as req
        self._requests = req
        self._base_url = base_url.rstrip("/")
        self._model = model
        logger.info(
            f"OllamaProvider initialised — base_url={self._base_url}, "
            f"model={self._model}"
        )

    def _check_ollama_running(self) -> None:
        """Raise a helpful error if Ollama isn't running."""
        try:
            self._requests.get(f"{self._base_url}/api/tags", timeout=3)
        except Exception:
            raise ConnectionError(
                f"Cannot reach Ollama at {self._base_url}. "
                "Make sure Ollama is running: https://ollama.com\n"
                f"Then pull your model: ollama pull {self._model}"
            )

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        self._check_ollama_running()

        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 4096},
        }
        if system:
            payload["system"] = system

        response = self._requests.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=300,   # local models can be slow — allow 5 min
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("response", "")

        return LLMResponse(
            content=content,
            provider="ollama",
            model=self._model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
        )

    def provider_name(self) -> str:
        return "ollama"


# ─────────────────────────────────────────────────────────────
# Stub provider — Phase 1 only, no LLM calls
# ─────────────────────────────────────────────────────────────

class StubProvider(BaseLLMProvider):
    """
    Returns hardcoded test output.
    Used in Phase 1 before any real LLM integration.
    Lets the full pipeline run without API keys.
    """

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        logger.warning("StubProvider is active — returning placeholder test code.")
        stub_test = '''
import pytest

def test_placeholder():
    """Placeholder test generated by StubProvider.
    Replace this with real LLM integration in Phase 2."""
    assert True
'''
        return LLMResponse(
            content=stub_test,
            provider="stub",
            model="stub",
        )

    def provider_name(self) -> str:
        return "stub"


# ─────────────────────────────────────────────────────────────
# LLMClient — the only class the rest of UnitForge uses
# ─────────────────────────────────────────────────────────────

class LLMClient:
    """
    Thin wrapper around whichever provider is configured.
    The rest of UnitForge only ever imports and uses this class.

    Example:
        client = LLMClient.from_env()
        response = client.generate(prompt="Write a test for...")
        print(response.content)
    """

    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider

    @classmethod
    def from_env(cls) -> "LLMClient":
        """
        Build an LLMClient from environment variables.
        Reads LLM_PROVIDER and the relevant keys automatically.
        Falls back to StubProvider if nothing is configured.
        """
        llm_provider = os.getenv("LLM_PROVIDER", "stub").lower().strip()

        if llm_provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "LLM_PROVIDER=claude requires ANTHROPIC_API_KEY to be set.\n"
                    "Get your key at https://console.anthropic.com\n"
                    "Or switch to free usage: set LLM_PROVIDER=ollama in .env"
                )
            return cls(ClaudeProvider(api_key=api_key))

        if llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", OpenAIProvider.DEFAULT_MODEL)
            if not api_key:
                raise EnvironmentError(
                    "LLM_PROVIDER=openai requires OPENAI_API_KEY to be set.\n"
                    "Or switch to free usage: set LLM_PROVIDER=ollama in .env"
                )
            return cls(OpenAIProvider(api_key=api_key, model=model))

        if llm_provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", OllamaProvider.DEFAULT_BASE_URL)
            model = os.getenv("OLLAMA_MODEL", OllamaProvider.DEFAULT_MODEL)
            return cls(OllamaProvider(base_url=base_url, model=model))

        if llm_provider == "stub":
            logger.info("Using StubProvider — no real LLM calls will be made.")
            return cls(StubProvider())

        raise ValueError(
            f"Unknown LLM_PROVIDER='{llm_provider}'. "
            "Valid options: claude | openai | ollama | stub"
        )

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a response from the configured provider."""
        logger.info(f"LLMClient.generate() using provider={self._provider.provider_name()}")
        return self._provider.generate(prompt=prompt, system=system)

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name()
