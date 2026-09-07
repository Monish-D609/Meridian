"""
Meridian — Industry Comparison Engine: Positioning Summary Generator.

Generates a plain-language, date-stamped positioning summary for a model.

Example output:
  "Model X is Frontier-tier on coding and mathematics, Strong-tier on reasoning
   and summarization, and Weak-tier on long-context and creative writing,
   relative to current industry baselines (captured 2024-09-01, illustrative).
   It hallucinates at a rate of 15% on factual tasks (claim-level). Mean latency:
   342ms. Estimated cost: $0.00/call (free tier)."

This is the key UX differentiator (PRD §7): lead with positioning narrative, not raw numbers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.comparison.capability_profile import CapabilityProfile
from app.comparison.tier_classifier import Tier


@dataclass
class PositioningSummary:
    model_id: str
    model_display_name: str
    headline: str           # one-line summary
    narrative: str          # full positioning paragraph
    tier_breakdown: dict[str, str]           # category → tier label
    strongest_strengths: list[str]           # natural language strength bullets
    key_weaknesses: list[str]                # natural language weakness bullets
    baseline_disclaimer: str                 # always shown; includes date + placeholder flag
    generated_at: str                        # ISO timestamp


def _category_display(slug: str) -> str:
    """Convert a slug to a human-readable category name."""
    mapping = {
        "coding": "coding",
        "mathematics": "mathematics",
        "reasoning": "reasoning",
        "creative_writing": "creative writing",
        "summarization": "summarization",
        "factual_qa": "factual QA",
        "long_context": "long-context reasoning",
    }
    return mapping.get(slug, slug.replace("_", " "))


def generate_positioning_summary(
    profile: CapabilityProfile,
    model_display_name: str,
    hallucination_rate: Optional[float] = None,
    mean_latency_ms: Optional[int] = None,
    total_cost_usd: Optional[float] = None,
    is_free_tier: bool = True,
) -> PositioningSummary:
    """
    Generate a plain-language positioning summary from a CapabilityProfile.

    All comparisons are relative to the baseline set, with date and placeholder
    status always disclosed (PRD §7 — Trustworthiness of comparison).
    """
    from datetime import datetime, timezone

    tiers = profile.tiers

    # Group categories by tier
    by_tier: dict[str, list[str]] = {t.value: [] for t in Tier}
    for slug, tier_result in tiers.items():
        display = _category_display(slug)
        by_tier[tier_result.tier.value].append(display)

    # Build tier phrases
    tier_phrases = []
    for tier_label in [Tier.FRONTIER.value, Tier.STRONG.value, Tier.MID.value, Tier.WEAK.value]:
        cats = by_tier.get(tier_label, [])
        if cats:
            cats_str = ", ".join(cats[:-1]) + (" and " + cats[-1] if len(cats) > 1 else cats[0])
            tier_phrases.append(f"{tier_label}-tier on {cats_str}")

    # Narrative body
    if tier_phrases:
        tier_sentence = f"{model_display_name} is " + "; ".join(tier_phrases) + "."
    else:
        tier_sentence = f"{model_display_name} could not be fully tiered (insufficient baseline data)."

    # Reliability sentence
    reliability_sentence = ""
    if hallucination_rate is not None:
        hr_pct = round(hallucination_rate * 100, 1)
        if hr_pct < 10:
            reliability_label = "very low"
        elif hr_pct < 25:
            reliability_label = "moderate"
        elif hr_pct < 50:
            reliability_label = "high"
        else:
            reliability_label = "very high"
        reliability_sentence = (
            f" It shows a {reliability_label} hallucination rate of {hr_pct}% "
            f"on factual tasks (claim-level, where measurable)."
        )

    # Efficiency sentence
    efficiency_parts = []
    if mean_latency_ms is not None:
        efficiency_parts.append(f"mean latency {mean_latency_ms}ms")
    if total_cost_usd is not None and is_free_tier:
        efficiency_parts.append("free-tier cost ($0.00/call)")
    elif total_cost_usd is not None:
        efficiency_parts.append(f"estimated cost ${total_cost_usd:.6f}/call")
    efficiency_sentence = ""
    if efficiency_parts:
        efficiency_sentence = " Efficiency: " + ", ".join(efficiency_parts) + "."

    # Baseline disclaimer (always shown, PRD §7)
    placeholder_note = " [ILLUSTRATIVE BASELINES — not real measurements]" if profile.is_placeholder_baseline else ""
    disclaimer = (
        f"Positioned against industry baselines captured {profile.baseline_captured_date}"
        f"{placeholder_note}. Tier thresholds: Frontier ≥80th percentile, Strong ≥60th, Mid ≥40th."
    )

    # Full narrative
    narrative = tier_sentence + reliability_sentence + efficiency_sentence

    # Headline (one line)
    top_cats = by_tier.get(Tier.FRONTIER.value, []) + by_tier.get(Tier.STRONG.value, [])
    weak_cats = by_tier.get(Tier.WEAK.value, [])
    if top_cats and weak_cats:
        headline = (
            f"{profile.overall_tier}-tier overall · "
            f"Strong at: {', '.join(top_cats[:2])} · "
            f"Weak at: {', '.join(weak_cats[:2])}"
        )
    elif top_cats:
        headline = f"{profile.overall_tier}-tier · Strong across: {', '.join(top_cats[:3])}"
    else:
        headline = f"{profile.overall_tier}-tier overall"

    # Strength/weakness bullets
    strengths = [f"{_category_display(s)} ({profile.tiers[s].tier.value}-tier)" for s in profile.strongest_categories if s in profile.tiers]
    weaknesses = [f"{_category_display(w)} ({profile.tiers[w].tier.value}-tier)" for w in profile.weakest_categories if w in profile.tiers]

    return PositioningSummary(
        model_id=profile.model_id,
        model_display_name=model_display_name,
        headline=headline,
        narrative=narrative,
        tier_breakdown={slug: tr.tier.value for slug, tr in tiers.items()},
        strongest_strengths=strengths,
        key_weaknesses=weaknesses,
        baseline_disclaimer=disclaimer,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
