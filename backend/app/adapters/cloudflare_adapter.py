"""
Meridian — Cloudflare Workers AI Adapter.

Cloudflare Workers AI provides free inference (10,000 Neurons/day).
Models are generally smaller/lower-capability than Groq/Gemini but useful
as a fallback when other quotas are exhausted.

Endpoint: https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}
Auth: Bearer CLOUDFLARE_API_TOKEN
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from app.adapters.base import AdapterResponse, BaseAdapter


class CloudflareAdapter(BaseAdapter):
    provider_name = "cloudflare"
    default_max_tokens = 512
    default_temperature = 0.0
    _base_url = "https://api.cloudflare.com/client/v4/accounts"
    _timeout = 60.0

    def is_configured(self) -> bool:
        return bool(
            os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
            and os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
        )

    async def _call_api(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> AdapterResponse:
        account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
        api_token = os.environ["CLOUDFLARE_API_TOKEN"]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "messages": messages,
            "max_tokens": max_tokens,
        }
        # Cloudflare does not support temperature on all models; omit if 0
        if temperature > 0:
            payload["temperature"] = temperature

        url = f"{self._base_url}/{account_id}/ai/run/{model_id}"

        start = self._measure_start()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        latency_ms = self._measure_latency_ms(start)
        data = response.json()

        if not data.get("success"):
            errors = data.get("errors", [])
            raise ValueError(f"Cloudflare AI error: {errors}")

        result = data.get("result", {})
        # Cloudflare returns {"response": "...", "usage": {...}}
        text = result.get("response", "")
        usage = result.get("usage", {})

        return AdapterResponse(
            text=text,
            input_tokens=usage.get("input_tokens") or usage.get("prompt_tokens"),
            output_tokens=usage.get("output_tokens") or usage.get("completion_tokens"),
            latency_ms=latency_ms,
            model_id=model_id,
            provider=self.provider_name,
            raw=data,
        )
