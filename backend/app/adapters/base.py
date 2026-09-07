"""
Meridian — Base Adapter Interface.

Every LLM provider adapter must implement this interface.
The rest of the system (Evaluation Engine, Benchmark Manager) only ever
calls adapters through this interface — never directly.

Design goals (per SAD §3.4):
- One adapter per provider
- Common call() signature: prompt, params → AdapterResponse
- Adapters own provider-specific auth, rate-limit backoff, error normalization
- The rest of the system never sees provider-specific exceptions
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Shared response dataclass
# ---------------------------------------------------------------------------
@dataclass
class AdapterResponse:
    """
    Normalized response from any LLM provider adapter.

    All fields that cannot be determined should be None — never fabricated.
    latency_ms: wall-clock time from request start to response received.
    raw: the full, unmodified provider response payload (for auditability).
    """
    text: str                           # the model's generated text
    input_tokens: Optional[int]         # prompt token count (None if unavailable)
    output_tokens: Optional[int]        # completion token count (None if unavailable)
    latency_ms: int                     # measured wall-clock latency
    model_id: str                       # the external model ID used
    provider: str                       # the provider name
    raw: dict[str, Any] = field(default_factory=dict)   # full raw provider response

    @property
    def total_tokens(self) -> Optional[int]:
        if self.input_tokens is not None and self.output_tokens is not None:
            return self.input_tokens + self.output_tokens
        return None


# ---------------------------------------------------------------------------
# Sentinel: returned when a call fails non-fatally (quota, transient error)
# ---------------------------------------------------------------------------
@dataclass
class AdapterError:
    """
    Returned instead of raising an exception on recoverable failures.
    The Benchmark Manager uses this to mark the cell as failed without
    aborting the overall run (SRS FR-3.3).
    """
    error_type: str          # 'rate_limit' | 'quota_exceeded' | 'timeout' | 'api_error' | 'config_error'
    message: str
    provider: str
    model_id: str
    status_code: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)
    retried: int = 0


# Union type for adapter call returns
AdapterResult = AdapterResponse | AdapterError


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class BaseAdapter(ABC):
    """
    Abstract base class for all LLM provider adapters.

    Subclasses must implement:
      - provider_name: str property
      - _call_api(): the actual HTTP call, may raise
      - is_configured(): True if the required env-vars/keys are present

    The public call() method wraps _call_api() with retry/backoff and
    error normalization so callers never see raw provider exceptions.
    """

    # Subclasses set these
    provider_name: str = "unknown"
    default_max_tokens: int = 1024
    default_temperature: float = 0.0   # deterministic by default for eval

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if this adapter has all required credentials."""
        ...

    @abstractmethod
    async def _call_api(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> AdapterResponse:
        """
        Make the actual API call. May raise any exception.
        The public call() wraps this with retry/backoff.
        """
        ...

    async def call(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> AdapterResult:
        """
        Public entry point. Wraps _call_api with:
          - Configuring defaults
          - Exponential backoff + retry on transient errors
          - Error normalization → AdapterError (never raises to the caller)
        """
        import asyncio
        import httpx

        if not self.is_configured():
            return AdapterError(
                error_type="config_error",
                message=f"{self.provider_name}: adapter is not configured (missing API key / env var).",
                provider=self.provider_name,
                model_id=model_id,
            )

        _max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        _temperature = temperature if temperature is not None else self.default_temperature

        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                result = await self._call_api(
                    model_id=model_id,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=_max_tokens,
                    temperature=_temperature,
                    **kwargs,
                )
                return result
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                body = {}
                try:
                    body = e.response.json()
                except Exception:
                    pass

                if status == 429:
                    # Rate limit — exponential backoff then retry
                    wait = 2 ** attempt
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait)
                        last_error = e
                        continue
                    return AdapterError(
                        error_type="rate_limit",
                        message=f"Rate limit hit on {self.provider_name} after {attempt + 1} attempts.",
                        provider=self.provider_name,
                        model_id=model_id,
                        status_code=status,
                        raw=body,
                        retried=attempt + 1,
                    )
                elif status in (402, 403):
                    return AdapterError(
                        error_type="quota_exceeded",
                        message=f"Quota or auth error on {self.provider_name}: HTTP {status}.",
                        provider=self.provider_name,
                        model_id=model_id,
                        status_code=status,
                        raw=body,
                        retried=attempt,
                    )
                else:
                    return AdapterError(
                        error_type="api_error",
                        message=f"API error on {self.provider_name}: HTTP {status}: {e}",
                        provider=self.provider_name,
                        model_id=model_id,
                        status_code=status,
                        raw=body,
                        retried=attempt,
                    )
            except httpx.TimeoutException as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    last_error = e
                    continue
                return AdapterError(
                    error_type="timeout",
                    message=f"Request timed out on {self.provider_name} after {attempt + 1} attempts.",
                    provider=self.provider_name,
                    model_id=model_id,
                    retried=attempt + 1,
                )
            except Exception as e:
                return AdapterError(
                    error_type="api_error",
                    message=f"Unexpected error on {self.provider_name}: {type(e).__name__}: {e}",
                    provider=self.provider_name,
                    model_id=model_id,
                    retried=attempt,
                )

        # Should not reach here
        return AdapterError(
            error_type="api_error",
            message=f"Exhausted retries on {self.provider_name}.",
            provider=self.provider_name,
            model_id=model_id,
        )

    def _measure_start(self) -> float:
        return time.monotonic()

    def _measure_latency_ms(self, start: float) -> int:
        return int((time.monotonic() - start) * 1000)
