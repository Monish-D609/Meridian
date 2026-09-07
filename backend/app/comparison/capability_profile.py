"""
Meridian — Industry Comparison Engine: Capability Profile.

Builds the per-model capability profile vector across all categories.
This vector is used to render the radar chart in the frontend.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.comparison.normalizer import NormalizedScore
from app.comparison.tier_classifier import TierResult


@dataclass
class CapabilityProfile:
    """
    A model's complete capability profile across all evaluated categories.
    Used for the radar chart visualization in the dashboard.
    """
    model_id: str
    model_display_name: str
    run_id: str

    # Raw scores per category [0, 1]
    raw_scores: dict[str, float]

    # Normalized scores (z-score, percentile)
    normalized_scores: dict[str, NormalizedScore]

    # Tier per category
    tiers: dict[str, TierResult]

    # Summary stats
    mean_raw_score: float
    overall_tier: str       # majority tier across categories
    strongest_categories: list[str]    # top 2 by percentile
    weakest_categories: list[str]      # bottom 2 by percentile

    # Baseline metadata
    baseline_captured_date: str    # date string from BaselineModel
    is_placeholder_baseline: bool


def build_capability_profile(
    model_id: str,
    model_display_name: str,
    run_id: str,
    raw_scores: dict[str, float],
    normalized_scores: dict[str, NormalizedScore],
    tiers: dict[str, TierResult],
    baseline_captured_date: str,
    is_placeholder_baseline: bool = False,
) -> CapabilityProfile:
    """Build a CapabilityProfile from pre-computed normalized scores and tiers."""
    from app.comparison.tier_classifier import Tier

    if not raw_scores:
        return CapabilityProfile(
            model_id=model_id,
            model_display_name=model_display_name,
            run_id=run_id,
            raw_scores={},
            normalized_scores={},
            tiers={},
            mean_raw_score=0.0,
            overall_tier=Tier.UNKNOWN.value,
            strongest_categories=[],
            weakest_categories=[],
            baseline_captured_date=baseline_captured_date,
            is_placeholder_baseline=is_placeholder_baseline,
        )

    mean_raw = sum(raw_scores.values()) / len(raw_scores)

    # Sort categories by percentile for strongest/weakest
    sorted_by_percentile = sorted(
        normalized_scores.items(),
        key=lambda kv: kv[1].percentile,
        reverse=True,
    )
    strongest = [slug for slug, _ in sorted_by_percentile[:2]]
    weakest   = [slug for slug, _ in sorted_by_percentile[-2:]][::-1]

    # Overall tier = tier that appears most often (mode), UNKNOWN if no tiers
    tier_counts: dict[str, int] = {}
    for t in tiers.values():
        tier_counts[t.tier.value] = tier_counts.get(t.tier.value, 0) + 1
    overall_tier = max(tier_counts, key=tier_counts.get) if tier_counts else Tier.UNKNOWN.value

    return CapabilityProfile(
        model_id=model_id,
        model_display_name=model_display_name,
        run_id=run_id,
        raw_scores=raw_scores,
        normalized_scores=normalized_scores,
        tiers=tiers,
        mean_raw_score=round(mean_raw, 4),
        overall_tier=overall_tier,
        strongest_categories=strongest,
        weakest_categories=weakest,
        baseline_captured_date=baseline_captured_date,
        is_placeholder_baseline=is_placeholder_baseline,
    )


def profile_to_radar_data(profile: CapabilityProfile) -> dict:
    """
    Convert a CapabilityProfile to the format expected by the frontend radar chart.
    Each category gets a normalized score (0–1) for the radar axis.
    """
    categories = list(profile.raw_scores.keys())
    return {
        "model_id": profile.model_id,
        "model_display_name": profile.model_display_name,
        "categories": categories,
        "raw_scores": [round(profile.raw_scores.get(c, 0), 4) for c in categories],
        "percentiles": [
            round(profile.normalized_scores[c].percentile, 4) if c in profile.normalized_scores else 0.5
            for c in categories
        ],
        "tiers": {c: profile.tiers[c].tier.value if c in profile.tiers else "Unknown" for c in categories},
        "overall_tier": profile.overall_tier,
        "mean_raw_score": profile.mean_raw_score,
        "strongest_categories": profile.strongest_categories,
        "weakest_categories": profile.weakest_categories,
    }
