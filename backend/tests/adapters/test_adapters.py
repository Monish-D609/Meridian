"""
Meridian — Unit Tests: Adapter Interface (mocked HTTP).

Tests that each adapter:
  1. Returns AdapterResponse on success
  2. Returns AdapterError on HTTP errors (never raises)
  3. Satisfies the common interface (same return types)
"""
import pytest
import httpx
import respx

from app.adapters.groq_adapter import GroqAdapter
from app.adapters.gemini_adapter import GeminiAdapter
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.adapters.base import AdapterResponse, AdapterError


# ---------------------------------------------------------------------------
# Groq Adapter Tests
# ---------------------------------------------------------------------------
class TestGroqAdapter:
    @pytest.mark.asyncio
    async def test_successful_call(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key-groq")
        adapter = GroqAdapter()

        mock_response = {
            "choices": [{"message": {"content": "Hello from Groq!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with respx.mock:
            respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            result = await adapter.call(
                model_id="llama-3.1-8b-instant",
                prompt="Hello",
            )

        assert isinstance(result, AdapterResponse)
        assert result.text == "Hello from Groq!"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        assert result.provider == "groq"
        assert result.model_id == "llama-3.1-8b-instant"
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_rate_limit_returns_adapter_error(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key-groq")
        adapter = GroqAdapter()

        with respx.mock:
            respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
                return_value=httpx.Response(429, json={"error": "rate limit"})
            )
            result = await adapter.call(
                model_id="llama-3.1-8b-instant",
                prompt="Hello",
                max_retries=1,   # only 1 retry for test speed
            )

        assert isinstance(result, AdapterError)
        assert result.error_type == "rate_limit"
        assert result.provider == "groq"

    @pytest.mark.asyncio
    async def test_unconfigured_returns_config_error(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        adapter = GroqAdapter()

        result = await adapter.call(model_id="llama-3.1-8b-instant", prompt="Hello")

        assert isinstance(result, AdapterError)
        assert result.error_type == "config_error"

    @pytest.mark.asyncio
    async def test_api_error_returns_adapter_error(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key-groq")
        adapter = GroqAdapter()

        with respx.mock:
            respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
                return_value=httpx.Response(500, json={"error": "server error"})
            )
            result = await adapter.call(
                model_id="llama-3.1-8b-instant",
                prompt="Hello",
                max_retries=1,
            )

        assert isinstance(result, AdapterError)
        assert result.error_type == "api_error"


# ---------------------------------------------------------------------------
# Gemini Adapter Tests
# ---------------------------------------------------------------------------
class TestGeminiAdapter:
    @pytest.mark.asyncio
    async def test_successful_call(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-gemini")
        adapter = GeminiAdapter()

        mock_response = {
            "candidates": [
                {"content": {"parts": [{"text": "Hello from Gemini!"}]}}
            ],
            "usageMetadata": {
                "promptTokenCount": 8,
                "candidatesTokenCount": 6,
            },
        }

        with respx.mock:
            respx.post(
                url__regex=r"https://generativelanguage\.googleapis\.com/.*"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            result = await adapter.call(
                model_id="gemini-1.5-flash-latest",
                prompt="Hello",
            )

        assert isinstance(result, AdapterResponse)
        assert result.text == "Hello from Gemini!"
        assert result.input_tokens == 8
        assert result.output_tokens == 6
        assert result.provider == "gemini"

    @pytest.mark.asyncio
    async def test_quota_exceeded_returns_adapter_error(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-gemini")
        adapter = GeminiAdapter()

        with respx.mock:
            respx.post(url__regex=r"https://generativelanguage\.googleapis\.com/.*").mock(
                return_value=httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED"}})
            )
            result = await adapter.call(
                model_id="gemini-1.5-flash-latest",
                prompt="Hello",
                max_retries=1,
            )

        assert isinstance(result, AdapterError)


# ---------------------------------------------------------------------------
# OpenRouter Adapter Tests
# ---------------------------------------------------------------------------
class TestOpenRouterAdapter:
    @pytest.mark.asyncio
    async def test_successful_call(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-openrouter")
        adapter = OpenRouterAdapter()

        mock_response = {
            "choices": [{"message": {"content": "Hello from OpenRouter!"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }

        with respx.mock:
            respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            result = await adapter.call(
                model_id="meta-llama/llama-3.1-8b-instruct:free",
                prompt="Hello",
            )

        assert isinstance(result, AdapterResponse)
        assert result.text == "Hello from OpenRouter!"
        assert result.provider == "openrouter"


# ---------------------------------------------------------------------------
# Common Interface Contract Tests
# ---------------------------------------------------------------------------
class TestAdapterInterface:
    """All adapters must return AdapterResponse or AdapterError — never raise."""

    @pytest.mark.asyncio
    async def test_adapter_response_has_required_fields(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        adapter = GroqAdapter()

        with respx.mock:
            respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
                return_value=httpx.Response(200, json={
                    "choices": [{"message": {"content": "test"}}],
                    "usage": {},
                })
            )
            result = await adapter.call(model_id="llama-3.1-8b-instant", prompt="test")

        assert isinstance(result, AdapterResponse)
        assert hasattr(result, "text")
        assert hasattr(result, "latency_ms")
        assert hasattr(result, "provider")
        assert hasattr(result, "model_id")
        assert hasattr(result, "raw")

    @pytest.mark.asyncio
    async def test_adapter_error_has_required_fields(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        adapter = GroqAdapter()
        result = await adapter.call(model_id="any", prompt="test")

        assert isinstance(result, AdapterError)
        assert hasattr(result, "error_type")
        assert hasattr(result, "message")
        assert hasattr(result, "provider")
        assert hasattr(result, "model_id")
