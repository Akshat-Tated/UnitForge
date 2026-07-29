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
# Gemini provider (Google AI Studio)
# ─────────────────────────────────────────────────────────────

class GeminiProvider(BaseLLMProvider):
    """
    Calls the Google Gemini API.
    Gemini 1.5 Flash is completely FREE with generous rate limits.
    No credit card needed.

    Setup:
        1. Go to https://aistudio.google.com
        2. Click Get API Key → Create API Key
        3. Set GOOGLE_API_KEY in .env
        4. Set LLM_PROVIDER=gemini in .env

    Recommended models:
        gemini-1.5-flash   → free, fast, good quality (recommended)
        gemini-1.5-pro     → paid, better quality
        gemini-2.0-flash   → free, latest, best free option
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        """
        Initialise the Gemini provider.

        Args:
            api_key: Your Google AI Studio API key
            model: The Gemini model to use
        """
        try:
            import google.generativeai as genai
            self._genai = genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed.\n"
                "Run: pip install google-generativeai"
            )
        self._genai.configure(api_key=api_key)
        self._model_name = model
        self._model = self._genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.2,      # lower = more consistent code
                "max_output_tokens": 4096,
            }
        )
        logger.info(f"GeminiProvider ready — model={self._model_name}")

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """
        Send a prompt to Gemini and return the response.

        Args:
            prompt: The test generation request
            system: System prompt (prepended to the user prompt)

        Returns:
            LLMResponse with generated test code
        """
        # Gemini combines system and user prompt into one
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        logger.debug(
            f"Calling Gemini API — model={self._model_name}, "
            f"prompt_len={len(full_prompt)}"
        )

        response = self._model.generate_content(full_prompt)

        # Extract text safely
        try:
            content = response.text
        except Exception:
            content = ""
            logger.warning("Gemini returned empty response")

        # Gemini does not expose token counts in the same way
        # Use character count as approximation
        return LLMResponse(
            content=content,
            provider="gemini",
            model=self._model_name,
            input_tokens=len(full_prompt) // 4,    # rough estimate
            output_tokens=len(content) // 4,
        )

    def provider_name(self) -> str:
        return "gemini"


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

        if llm_provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "LLM_PROVIDER=gemini but GOOGLE_API_KEY is not set.\n"
                    "Get a free key at https://aistudio.google.com\n"
                    "Then add GOOGLE_API_KEY=your-key to .env"
                )
            model = os.getenv("GEMINI_MODEL", GeminiProvider.DEFAULT_MODEL)
            return cls(GeminiProvider(api_key=api_key, model=model))

        if llm_provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", OllamaProvider.DEFAULT_BASE_URL)
            model = os.getenv("OLLAMA_MODEL", OllamaProvider.DEFAULT_MODEL)
            return cls(OllamaProvider(base_url=base_url, model=model))

        if llm_provider == "stub":
            logger.info("Using StubProvider — no real LLM calls will be made.")
            return cls(StubProvider())

        raise ValueError(
            f"Unknown LLM_PROVIDER='{llm_provider}'. "
            "Valid options: claude | openai | gemini | ollama | stub"
        )

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a response from the configured provider."""
        logger.info(f"LLMClient.generate() using provider={self._provider.provider_name()}")
        return self._provider.generate(prompt=prompt, system=system)

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name()
