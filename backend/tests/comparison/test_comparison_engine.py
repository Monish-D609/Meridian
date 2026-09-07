"""
Meridian — Unit Tests: Industry Comparison Engine.

Tests normalizer, tier_classifier, capability_profile with fixed synthetic inputs.
"""
import pytest
from app.comparison.normalizer import normalize_score, normalize_scores_batch
from app.comparison.tier_classifier import Tier, classify_tier, classify_tiers_batch
from app.comparison.summary_generator import generate_positioning_summary
from app.comparison.capability_profile import build_capability_profile


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------
class TestNormalizer:
    def test_above_all_baselines(self):
        """Score above all baselines → percentile=1.0"""
        ns = normalize_score(
            raw_score=0.95,
            baseline_scores=[0.70, 0.80, 0.85],
            category_slug="coding",
        )
        assert ns.percentile == pytest.approx(1.0)
        assert ns.z_score > 0

    def test_below_all_baselines(self):
        """Score below all baselines → percentile=0.0"""
        ns = normalize_score(
            raw_score=0.50,
            baseline_scores=[0.70, 0.80, 0.90],
            category_slug="coding",
        )
        assert ns.percentile == pytest.approx(0.0)
        assert ns.z_score < 0

    def test_midpoint_score(self):
        """Score in the middle → percentile ~0.33 (beats 1 of 3)"""
        ns = normalize_score(
            raw_score=0.75,
            baseline_scores=[0.70, 0.80, 0.90],
            category_slug="coding",
        )
        # Beats 1 out of 3 baselines (0.70)
        assert ns.percentile == pytest.approx(1/3, abs=0.01)

    def test_empty_baselines(self):
        """No baselines → percentile=0.5 (neutral)"""
        ns = normalize_score(
            raw_score=0.80,
            baseline_scores=[],
            category_slug="coding",
        )
        assert ns.percentile == pytest.approx(0.5)
        assert ns.baseline_count == 0

    def test_batch_normalization(self):
        """Batch normalization returns one result per category."""
        results = normalize_scores_batch(
            candidate_scores={"coding": 0.85, "mathematics": 0.70},
            baseline_by_category={
                "coding": [0.70, 0.80, 0.90],
                "mathematics": [0.60, 0.75, 0.85],
            }
        )
        assert "coding" in results
        assert "mathematics" in results
        assert 0.0 <= results["coding"].percentile <= 1.0


# ---------------------------------------------------------------------------
# Tier Classifier
# ---------------------------------------------------------------------------
class TestTierClassifier:
    def setup_method(self):
        """Set up a normalized score at each tier boundary."""
        from app.comparison.normalizer import NormalizedScore

        def ns(pct: float, slug: str = "coding") -> NormalizedScore:
            return NormalizedScore(
                category_slug=slug,
                raw_score=pct,
                z_score=(pct - 0.75) / 0.1,
                percentile=pct,
                baseline_mean=0.75,
                baseline_std=0.1,
                baseline_count=3,
                is_placeholder_baseline=False,
            )
        self._ns = ns

    def test_frontier_tier(self):
        result = classify_tier(self._ns(0.85), frontier_threshold=0.80)
        assert result.tier == Tier.FRONTIER

    def test_strong_tier(self):
        result = classify_tier(self._ns(0.65), strong_threshold=0.60, frontier_threshold=0.80)
        assert result.tier == Tier.STRONG

    def test_mid_tier(self):
        result = classify_tier(
            self._ns(0.45),
            frontier_threshold=0.80, strong_threshold=0.60, mid_threshold=0.40
        )
        assert result.tier == Tier.MID

    def test_weak_tier(self):
        result = classify_tier(
            self._ns(0.20),
            frontier_threshold=0.80, strong_threshold=0.60, mid_threshold=0.40
        )
        assert result.tier == Tier.WEAK

    def test_unknown_tier_no_baselines(self):
        from app.comparison.normalizer import NormalizedScore
        ns = NormalizedScore(
            category_slug="coding",
            raw_score=0.80,
            z_score=0.0,
            percentile=0.0,
            baseline_mean=0.0,
            baseline_std=0.0,
            baseline_count=0,      # no baselines → Unknown
            is_placeholder_baseline=True,
        )
        result = classify_tier(ns)
        assert result.tier == Tier.UNKNOWN

    def test_batch_classify(self):
        from app.comparison.normalizer import NormalizedScore

        def ns(pct, slug):
            return NormalizedScore(
                category_slug=slug, raw_score=pct, z_score=0.0,
                percentile=pct, baseline_mean=0.75, baseline_std=0.1,
                baseline_count=3, is_placeholder_baseline=False,
            )

        normalized = {
            "coding": ns(0.90, "coding"),
            "mathematics": ns(0.55, "mathematics"),
            "reasoning": ns(0.30, "reasoning"),
        }
        tiers = classify_tiers_batch(
            normalized,
            frontier_threshold=0.80, strong_threshold=0.60, mid_threshold=0.40
        )
        assert tiers["coding"].tier == Tier.FRONTIER
        assert tiers["mathematics"].tier == Tier.MID
        assert tiers["reasoning"].tier == Tier.WEAK


# ---------------------------------------------------------------------------
# Positioning Summary Generator
# ---------------------------------------------------------------------------
class TestSummaryGenerator:
    def _make_profile(self):
        from app.comparison.normalizer import NormalizedScore
        from app.comparison.tier_classifier import TierResult

        def ns(pct, slug):
            return NormalizedScore(
                category_slug=slug, raw_score=pct, z_score=0.0,
                percentile=pct, baseline_mean=0.75, baseline_std=0.1,
                baseline_count=3, is_placeholder_baseline=True,
            )

        def tr(tier, slug, pct):
            return TierResult(
                category_slug=slug, tier=tier, percentile=pct,
                z_score=0.0, description="", baseline_count=3,
                is_placeholder_baseline=True,
            )

        raw_scores = {"coding": 0.90, "mathematics": 0.45, "reasoning": 0.25}
        normalized = {k: ns(v, k) for k, v in raw_scores.items()}
        tiers = {
            "coding":      tr(Tier.FRONTIER, "coding",      0.90),
            "mathematics": tr(Tier.MID,      "mathematics", 0.45),
            "reasoning":   tr(Tier.WEAK,     "reasoning",   0.25),
        }
        return build_capability_profile(
            model_id="test-model-1",
            model_display_name="Test Model",
            run_id="test-run-1",
            raw_scores=raw_scores,
            normalized_scores=normalized,
            tiers=tiers,
            baseline_captured_date="2024-09-01",
            is_placeholder_baseline=True,
        )

    def test_summary_contains_tier_labels(self):
        profile = self._make_profile()
        summary = generate_positioning_summary(profile, "Test Model")
        assert "Frontier" in summary.narrative or "Frontier" in summary.headline
        assert "Weak" in summary.narrative or "Weak" in summary.headline

    def test_baseline_disclaimer_always_present(self):
        profile = self._make_profile()
        summary = generate_positioning_summary(profile, "Test Model")
        assert "2024-09-01" in summary.baseline_disclaimer
        assert "ILLUSTRATIVE" in summary.baseline_disclaimer   # placeholder flag

    def test_strongest_categories_populated(self):
        profile = self._make_profile()
        assert len(profile.strongest_categories) > 0

    def test_weakest_categories_populated(self):
        profile = self._make_profile()
        assert len(profile.weakest_categories) > 0

    def test_overall_tier_is_string(self):
        profile = self._make_profile()
        assert isinstance(profile.overall_tier, str)
        assert profile.overall_tier in [t.value for t in Tier]
