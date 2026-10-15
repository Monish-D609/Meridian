"""
Meridian — Google Gemini Adapter (Google AI Studio).

Uses the Google Generative AI REST API (AI Studio), NOT Vertex AI.
AI Studio has a perpetual free tier with no credit card required.
Gemini Flash is the primary LLM-as-a-Judge model.

Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
Auth: ?key=GEMINI_API_KEY (query param)
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from app.adapters.base import AdapterResponse, BaseAdapter


class GeminiAdapter(BaseAdapter):
    provider_name = "gemini"
    default_max_tokens = 1024
    default_temperature = 0.0
    _base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    _timeout = 90.0

    def is_configured(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY", "").strip())

    async def _call_api(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> AdapterResponse:
        api_key = os.environ["GEMINI_API_KEY"]

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}], "role": "user"}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        # Strip prefix and resolve model aliases if needed
        raw_model = model_id.strip()
        if raw_model.startswith("models/"):
            raw_model = raw_model[7:]

        ALIASES = {
            "gemini-1.5-flash": "gemini-2.5-flash",
            "gemini-1.5-flash-latest": "gemini-2.5-flash",
            "gemini-1.5-flash-001": "gemini-2.5-flash",
            "gemini-1.5-pro": "gemini-2.5-pro",
            "gemini-1.5-pro-latest": "gemini-2.5-pro",
        }
        resolved_model = ALIASES.get(raw_model, raw_model)

        url = f"{self._base_url}/{resolved_model}:generateContent?key={api_key}"

        start = self._measure_start()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()

        latency_ms = self._measure_latency_ms(start)
        data = response.json()

        # Extract text from first candidate
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"Gemini returned no candidates: {data}")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

        usage = data.get("usageMetadata", {})
        return AdapterResponse(
            text=text,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            latency_ms=latency_ms,
            model_id=model_id,
            provider=self.provider_name,
            raw=data,
        )
