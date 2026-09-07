"""
Meridian — Cost Scorer.

Estimates dollar cost for each RunResult based on a configurable pricing table.
All prices are per-1M tokens (input and output separately where applicable).
Free-tier models have cost = 0.0.

The pricing table is in-code but treated as configuration (easy to update
when provider pricing changes without modifying business logic).

SRS FR-7.x: Cost estimation + cost-vs-performance view.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SCORER_VERSION = "cost-scorer-v1.0"

# ---------------------------------------------------------------------------
# Pricing Table
# Cost per 1M tokens (USD). Use 0.0 for free-tier models.
# Prices as of September 2026 — update as needed.
# Source: provider pricing pages (Groq, Google AI Studio, OpenRouter).
# ---------------------------------------------------------------------------
PRICING_TABLE: dict[str, dict[str, float]] = {
    # Groq free models
    "groq::llama-3.1-8b-instant": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    "groq::gemma2-9b-it":         {"input_per_1m": 0.0, "output_per_1m": 0.0},
    "groq::llama-3.3-70b-versatile": {"input_per_1m": 0.59, "output_per_1m": 0.79},
    # Google AI Studio free models
    "gemini::gemini-1.5-flash-latest": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    "gemini::gemini-1.5-pro-latest":   {"input_per_1m": 0.0, "output_per_1m": 0.0},
    # OpenRouter free models
    "openrouter::meta-llama/llama-3.1-8b-instruct:free": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    "openrouter::google/gemma-2-9b-it:free":              {"input_per_1m": 0.0, "output_per_1m": 0.0},
    # Cloudflare Workers AI
    "cloudflare::@cf/meta/llama-3.1-8b-instruct": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    # NVIDIA NIM (free credits)
    "nvidia_nim::meta/llama-3.1-8b-instruct": {"input_per_1m": 0.0, "output_per_1m": 0.0},
}

# Fallback pricing for unknown models
_DEFAULT_PRICING: dict[str, float] = {"input_per_1m": 0.0, "output_per_1m": 0.0}


@dataclass
class CostScore:
    estimated_cost_usd: float
    input_cost_usd: float
    output_cost_usd: float
    pricing_source: str    # key used to look up pricing
    is_free_tier: bool
    scorer_version: str = SCORER_VERSION


def _get_pricing(provider: str, model_id: str) -> tuple[dict[str, float], str]:
    """Look up pricing for a provider+model combo. Returns (pricing_dict, key_used)."""
    key = f"{provider}::{model_id}"
    if key in PRICING_TABLE:
        return PRICING_TABLE[key], key

    # Try model_id only (some providers reuse model IDs)
    for table_key, pricing in PRICING_TABLE.items():
        if table_key.endswith(f"::{model_id}"):
            return pricing, table_key

    return _DEFAULT_PRICING, "default"


def score_cost(
    provider: str,
    model_id: str,
    input_tokens: Optional[int],
    output_tokens: Optional[int],
) -> CostScore:
    """
    Estimate cost in USD for one inference call.
    Returns 0.0 cost for free-tier models or when token counts are unavailable.
    """
    pricing, key_used = _get_pricing(provider, model_id)

    if input_tokens is None and output_tokens is None:
        return CostScore(
            estimated_cost_usd=0.0,
            input_cost_usd=0.0,
            output_cost_usd=0.0,
            pricing_source=key_used,
            is_free_tier=True,
        )

    input_cost = ((input_tokens or 0) / 1_000_000) * pricing["input_per_1m"]
    output_cost = ((output_tokens or 0) / 1_000_000) * pricing["output_per_1m"]
    total_cost = input_cost + output_cost

    is_free = pricing["input_per_1m"] == 0.0 and pricing["output_per_1m"] == 0.0

    return CostScore(
        estimated_cost_usd=round(total_cost, 8),
        input_cost_usd=round(input_cost, 8),
        output_cost_usd=round(output_cost, 8),
        pricing_source=key_used,
        is_free_tier=is_free,
    )


def aggregate_cost(scores: list[CostScore]) -> dict:
    """Aggregate cost scores across multiple tasks for one model."""
    if not scores:
        return {}
    total = sum(s.estimated_cost_usd for s in scores)
    return {
        "total_cost_usd": round(total, 8),
        "mean_cost_per_call_usd": round(total / len(scores), 10),
        "task_count": len(scores),
        "is_all_free_tier": all(s.is_free_tier for s in scores),
    }
