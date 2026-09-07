"""
Meridian — Industry Comparison Engine: Tier Classifier.

Assigns a Tier label to each category based on the normalized percentile score.
Thresholds are configurable via app settings (SRS FR-6.x).

Tiers:
  Frontier  : >= TIER_FRONTIER_THRESHOLD percentile  (default: 80th)
  Strong    : >= TIER_STRONG_THRESHOLD percentile    (default: 60th)
  Mid       : >= TIER_MID_THRESHOLD percentile       (default: 40th)
  Weak      : below MID threshold
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.comparison.normalizer import NormalizedScore
from app.core.config import settings


class Tier(str, Enum):
    FRONTIER = "Frontier"
    STRONG   = "Strong"
    MID      = "Mid"
    WEAK     = "Weak"
    UNKNOWN  = "Unknown"    # when no baseline data is available


# Human-readable descriptions for positioning statements
TIER_DESCRIPTIONS: dict[Tier, str] = {
    Tier.FRONTIER: "performs at or above frontier-model level",
    Tier.STRONG:   "performs strongly relative to industry baselines",
    Tier.MID:      "performs at a mid-tier level relative to industry baselines",
    Tier.WEAK:     "underperforms relative to current industry baselines",
    Tier.UNKNOWN:  "cannot be positioned (insufficient baseline data)",
}


@dataclass
class TierResult:
    category_slug: str
    tier: Tier
    percentile: float
    z_score: float
    description: str
    baseline_count: int
    is_placeholder_baseline: bool


def classify_tier(
    normalized: NormalizedScore,
    frontier_threshold: float | None = None,
    strong_threshold: float | None = None,
    mid_threshold: float | None = None,
) -> TierResult:
    """
    Classify a normalized score into a Tier.
    Uses settings thresholds by default; thresholds can be overridden per-run.
    """
    ft = frontier_threshold if frontier_threshold is not None else settings.TIER_FRONTIER_THRESHOLD
    st = strong_threshold   if strong_threshold   is not None else settings.TIER_STRONG_THRESHOLD
    mt = mid_threshold      if mid_threshold      is not None else settings.TIER_MID_THRESHOLD

    if normalized.baseline_count == 0:
        tier = Tier.UNKNOWN
    elif normalized.percentile >= ft:
        tier = Tier.FRONTIER
    elif normalized.percentile >= st:
        tier = Tier.STRONG
    elif normalized.percentile >= mt:
        tier = Tier.MID
    else:
        tier = Tier.WEAK

    return TierResult(
        category_slug=normalized.category_slug,
        tier=tier,
        percentile=normalized.percentile,
        z_score=normalized.z_score,
        description=TIER_DESCRIPTIONS[tier],
        baseline_count=normalized.baseline_count,
        is_placeholder_baseline=normalized.is_placeholder_baseline,
    )


def classify_tiers_batch(
    normalized_scores: dict[str, NormalizedScore],
    frontier_threshold: float | None = None,
    strong_threshold: float | None = None,
    mid_threshold: float | None = None,
) -> dict[str, TierResult]:
    """Classify all category scores in one call."""
    return {
        slug: classify_tier(ns, frontier_threshold, strong_threshold, mid_threshold)
        for slug, ns in normalized_scores.items()
    }
