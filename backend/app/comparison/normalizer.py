"""
Meridian — Industry Comparison Engine: Normalizer.

Normalizes a candidate model's raw category scores against the Baseline Set
using z-score and percentile normalization.

This module is deliberately isolated from the Evaluation Engine (SAD §3.6)
so the Baseline Set can be refreshed without touching scoring logic.

Algorithm:
  1. Collect all baseline_scores for this category from the DB (the distribution)
  2. Compute z-score: z = (candidate_score - mean) / std
  3. Compute percentile rank: fraction of baseline models the candidate outperforms
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedScore:
    category_slug: str
    raw_score: float            # candidate's raw score [0, 1]
    z_score: float              # z-score vs baseline distribution
    percentile: float           # percentile rank [0, 1] vs baseline set
    baseline_mean: float        # mean of baseline distribution
    baseline_std: float         # std of baseline distribution
    baseline_count: int         # number of baseline models in distribution
    is_placeholder_baseline: bool  # True if using placeholder/seed baselines


def normalize_score(
    raw_score: float,
    baseline_scores: list[float],    # all baseline models' scores for this category
    category_slug: str,
    is_placeholder_baseline: bool = False,
) -> NormalizedScore:
    """
    Normalize a candidate model's raw score against the baseline distribution.

    baseline_scores: list of raw scores (0–1) from all baseline models.
    """
    if not baseline_scores:
        return NormalizedScore(
            category_slug=category_slug,
            raw_score=raw_score,
            z_score=0.0,
            percentile=0.5,
            baseline_mean=raw_score,
            baseline_std=1.0,
            baseline_count=0,
            is_placeholder_baseline=is_placeholder_baseline,
        )

    n = len(baseline_scores)
    mean = sum(baseline_scores) / n
    variance = sum((s - mean) ** 2 for s in baseline_scores) / n
    std = variance ** 0.5

    # Z-score: how many standard deviations above/below the mean
    z = (raw_score - mean) / (std if std > 0 else 1.0)

    # Percentile rank: fraction of baseline scores the candidate beats
    percentile = sum(1 for s in baseline_scores if raw_score > s) / n

    return NormalizedScore(
        category_slug=category_slug,
        raw_score=raw_score,
        z_score=round(z, 4),
        percentile=round(percentile, 4),
        baseline_mean=round(mean, 4),
        baseline_std=round(std, 4),
        baseline_count=n,
        is_placeholder_baseline=is_placeholder_baseline,
    )


def normalize_scores_batch(
    candidate_scores: dict[str, float],              # category_slug → raw_score
    baseline_by_category: dict[str, list[float]],   # category_slug → [baseline raw scores]
    is_placeholder_baseline: bool = False,
) -> dict[str, NormalizedScore]:
    """
    Normalize scores for all categories in one call.
    Returns a dict of category_slug → NormalizedScore.
    """
    return {
        slug: normalize_score(
            raw_score=score,
            baseline_scores=baseline_by_category.get(slug, []),
            category_slug=slug,
            is_placeholder_baseline=is_placeholder_baseline,
        )
        for slug, score in candidate_scores.items()
    }
