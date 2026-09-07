"""
Meridian — OpenRouter Adapter.

OpenRouter provides a unified API to hundreds of models, including free `:free`
models that require no payment. Free tier: 20 RPM, 50-1000 RPD.

Endpoint: https://openrouter.ai/api/v1/chat/completions (OpenAI-compatible)
Auth: Bearer OPENROUTER_API_KEY
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from app.adapters.base import AdapterResponse, BaseAdapter

_APP_SITE_URL = "https://github.com/your-org/meridian"
_APP_NAME = "Meridian LLM Eval Platform"


class OpenRouterAdapter(BaseAdapter):
    provider_name = "openrouter"
    default_max_tokens = 1024
    default_temperature = 0.0
    _base_url = "https://openrouter.ai/api/v1"
    _timeout = 120.0

    def is_configured(self) -> bool:
        return bool(os.getenv("OPENROUTER_API_KEY", "").strip())

    async def _call_api(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> AdapterResponse:
        api_key = os.environ["OPENROUTER_API_KEY"]
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        start = self._measure_start()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    # OpenRouter-recommended headers for tracking/routing
                    "HTTP-Referer": _APP_SITE_URL,
                    "X-Title": _APP_NAME,
                },
                json=payload,
            )
            response.raise_for_status()

        latency_ms = self._measure_latency_ms(start)
        data = response.json()

        # OpenRouter may return an error object in the body even with 200
        if "error" in data:
            err = data["error"]
            raise httpx.HTTPStatusError(
                message=str(err),
                request=response.request,
                response=response,
            )

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return AdapterResponse(
            text=choice["message"]["content"],
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_ms=latency_ms,
            model_id=model_id,
            provider=self.provider_name,
            raw=data,
        )
