"""
Meridian — Efficiency Scorer.

Aggregates latency and token usage from RunResults into per-model
efficiency metrics for comparison (SRS FR-7.x).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SCORER_VERSION = "efficiency-scorer-v1.0"


@dataclass
class EfficiencyScore:
    latency_ms: int
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    tokens_per_second: Optional[float]   # output_tokens / (latency_ms / 1000)
    scorer_version: str = SCORER_VERSION


def score_efficiency(
    latency_ms: int,
    input_tokens: Optional[int],
    output_tokens: Optional[int],
) -> EfficiencyScore:
    """
    Compute efficiency metrics from raw adapter response data.
    tokens_per_second is the key throughput metric.
    """
    total = None
    if input_tokens is not None and output_tokens is not None:
        total = input_tokens + output_tokens

    tps = None
    if output_tokens is not None and latency_ms > 0:
        tps = round(output_tokens / (latency_ms / 1000.0), 2)

    return EfficiencyScore(
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total,
        tokens_per_second=tps,
    )


def aggregate_efficiency(scores: list[EfficiencyScore]) -> dict:
    """
    Aggregate efficiency scores across multiple tasks for one model.
    Returns mean/median/p95 latency, mean token counts, mean TPS.
    """
    if not scores:
        return {}

    latencies = [s.latency_ms for s in scores]
    latencies.sort()
    n = len(latencies)
    p95_idx = max(0, int(n * 0.95) - 1)

    out_tokens = [s.output_tokens for s in scores if s.output_tokens is not None]
    tps_values = [s.tokens_per_second for s in scores if s.tokens_per_second is not None]

    return {
        "mean_latency_ms": round(sum(latencies) / n),
        "median_latency_ms": latencies[n // 2],
        "p95_latency_ms": latencies[p95_idx],
        "min_latency_ms": latencies[0],
        "max_latency_ms": latencies[-1],
        "mean_output_tokens": round(sum(out_tokens) / len(out_tokens)) if out_tokens else None,
        "mean_tokens_per_second": round(sum(tps_values) / len(tps_values), 2) if tps_values else None,
        "task_count": n,
    }
