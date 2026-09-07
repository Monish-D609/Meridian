"""
Meridian — Groq Adapter.

Groq provides ultra-fast LLM inference using the OpenAI-compatible chat
completions endpoint. Free tier: ~30 RPM, ~6k TPM (model-specific).

Endpoint: https://api.groq.com/openai/v1/chat/completions
Auth: Bearer GROQ_API_KEY
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from app.adapters.base import AdapterResponse, BaseAdapter


class GroqAdapter(BaseAdapter):
    provider_name = "groq"
    default_max_tokens = 1024
    default_temperature = 0.0
    _base_url = "https://api.groq.com/openai/v1"
    _timeout = 60.0

    def is_configured(self) -> bool:
        return bool(os.getenv("GROQ_API_KEY", "").strip())

    async def _call_api(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> AdapterResponse:
        api_key = os.environ["GROQ_API_KEY"]
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
                },
                json=payload,
            )
            response.raise_for_status()

        latency_ms = self._measure_latency_ms(start)
        data = response.json()

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
