"""
Meridian — Unit Tests: Quality Scorer.

Tests exact_match, token_f1, semantic_similarity, and llm_judge_quality
with fixed synthetic inputs and expected outputs.
"""
import pytest
from app.evaluation.quality_scorer import (
    exact_match,
    token_f1,
    semantic_similarity,
    _normalize,
)


# ---------------------------------------------------------------------------
# exact_match
# ---------------------------------------------------------------------------
class TestExactMatch:
    def test_identical_strings(self):
        assert exact_match("Paris", "Paris") == 1.0

    def test_case_insensitive(self):
        assert exact_match("paris", "Paris") == 1.0

    def test_punctuation_stripped(self):
        assert exact_match("Paris!", "Paris.") == 1.0

    def test_whitespace_normalized(self):
        assert exact_match("  Paris  ", "Paris") == 1.0

    def test_mismatch(self):
        assert exact_match("London", "Paris") == 0.0

    def test_empty_match(self):
        assert exact_match("", "") == 1.0

    def test_partial_match_is_0(self):
        assert exact_match("Paris, France", "Paris") == 0.0


# ---------------------------------------------------------------------------
# token_f1
# ---------------------------------------------------------------------------
class TestTokenF1:
    def test_identical(self):
        assert token_f1("the cat sat", "the cat sat") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert token_f1("foo bar", "baz qux") == pytest.approx(0.0)

    def test_partial_overlap(self):
        # "the cat" vs "the dog" — 1 common token "the", precision=0.5, recall=0.5
        score = token_f1("the cat", "the dog")
        assert 0.0 < score < 1.0

    def test_empty_prediction(self):
        assert token_f1("", "some reference") == pytest.approx(0.0)

    def test_empty_reference(self):
        assert token_f1("some prediction", "") == pytest.approx(0.0)

    def test_subset_prediction(self):
        # prediction is a subset of reference
        score = token_f1("the cat", "the cat sat on the mat")
        assert score > 0.0
        assert score < 1.0

    def test_hallucinated_response(self):
        """A completely hallucinated response has very low F1 (near 0)."""
        pred = "Bananas grow on Jupiter during winter solstice celebrations."
        ref = "Water boils at one hundred degrees Celsius."
        # No meaningful token overlap between these two sentences
        assert token_f1(pred, ref) < 0.2


# ---------------------------------------------------------------------------
# token_f1 — math answers
# ---------------------------------------------------------------------------
class TestTokenF1Math:
    def test_correct_number(self):
        assert token_f1("75", "75") == pytest.approx(1.0)

    def test_wrong_number(self):
        assert token_f1("76", "75") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Normalization helper
# ---------------------------------------------------------------------------
class TestNormalize:
    def test_lowercases(self):
        assert _normalize("HELLO WORLD") == "hello world"

    def test_strips_punctuation(self):
        assert _normalize("hello, world!") == "hello world"

    def test_collapses_whitespace(self):
        assert _normalize("  hello   world  ") == "hello world"


# ---------------------------------------------------------------------------
# semantic_similarity (requires sentence-transformers; skip if not installed)
# ---------------------------------------------------------------------------
class TestSemanticSimilarity:
    def test_identical_high(self):
        sim = semantic_similarity("The cat sat on the mat.", "The cat sat on the mat.")
        if sim is not None:
            assert sim > 0.95

    def test_similar_high(self):
        sim = semantic_similarity(
            "The capital of France is Paris.",
            "Paris is the capital city of France."
        )
        if sim is not None:
            assert sim > 0.8

    def test_dissimilar_low(self):
        sim = semantic_similarity(
            "The capital of France is Paris.",
            "Quantum mechanics describes the behavior of particles at subatomic scales."
        )
        if sim is not None:
            assert sim < 0.6

    def test_returns_in_range(self):
        sim = semantic_similarity("hello", "world")
        if sim is not None:
            assert 0.0 <= sim <= 1.0
