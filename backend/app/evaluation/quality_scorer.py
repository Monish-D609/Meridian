"""
Meridian — Quality Scorer.

Computes quality metrics for a model response against a reference:

  Closed tasks (exact-match/F1 scorable):
    - exact_match    : 1.0 if normalized strings match, 0.0 otherwise
    - f1             : token-level F1 score
    - semantic_sim   : cosine similarity via sentence-transformers (lazy-loaded)

  Open-ended tasks (LLM-judge):
    - llm_judge_quality : 0–1 score from an LLM evaluator with structured rubric

The LLM-judge identity (provider, model, version) is returned with every score
for reproducibility (SRS FR-3.5, NFR-3.2).
"""
from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import Optional

SCORER_VERSION = "quality-scorer-v1.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace (standard QA normalization)."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> list[str]:
    return _normalize(text).split()


# ---------------------------------------------------------------------------
# Exact Match
# ---------------------------------------------------------------------------
def exact_match(prediction: str, reference: str) -> float:
    """
    Returns 1.0 if prediction matches reference after normalization, else 0.0.
    Standard closed-QA metric.
    """
    return 1.0 if _normalize(prediction) == _normalize(reference) else 0.0


# ---------------------------------------------------------------------------
# Token-level F1
# ---------------------------------------------------------------------------
def token_f1(prediction: str, reference: str) -> float:
    """
    Token-level F1 score between prediction and reference (SQuAD-style).
    Returns value in [0, 1].
    """
    pred_tokens = _tokenize(prediction)
    ref_tokens = _tokenize(reference)

    if not pred_tokens or not ref_tokens:
        return 0.0

    pred_counts: dict[str, int] = {}
    for t in pred_tokens:
        pred_counts[t] = pred_counts.get(t, 0) + 1

    ref_counts: dict[str, int] = {}
    for t in ref_tokens:
        ref_counts[t] = ref_counts.get(t, 0) + 1

    common = sum(
        min(pred_counts.get(t, 0), ref_counts.get(t, 0))
        for t in ref_counts
    )
    if common == 0:
        return 0.0

    precision = common / len(pred_tokens)
    recall = common / len(ref_tokens)
    return (2 * precision * recall) / (precision + recall)


# ---------------------------------------------------------------------------
# Semantic Similarity (lazy-loaded sentence-transformers)
# ---------------------------------------------------------------------------
_st_model = None


def _get_st_model():
    global _st_model
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            _st_model = None
    return _st_model


def semantic_similarity(prediction: str, reference: str) -> Optional[float]:
    """
    Cosine similarity between sentence embeddings of prediction and reference.
    Returns None if sentence-transformers is not available.
    Uses 'all-MiniLM-L6-v2' (small, fast, free, local).
    """
    model = _get_st_model()
    if model is None:
        return None

    import numpy as np  # type: ignore

    embeddings = model.encode([prediction, reference], convert_to_numpy=True)
    a, b = embeddings[0], embeddings[1]
    cosine = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    return max(0.0, min(1.0, cosine))


# ---------------------------------------------------------------------------
# LLM-as-a-Judge for open-ended tasks
# ---------------------------------------------------------------------------

_JUDGE_PROMPT_TEMPLATE = """\
You are an expert evaluator assessing the quality of an AI assistant's response to a task.

## Task
{task_prompt}

## Model Response
{response}

## Reference Answer (if available)
{reference}

## Evaluation Rubric
Score the response on a scale of 0 to 10 across these dimensions:
1. **Accuracy / Correctness** (0-10): Is the response factually correct and complete?
2. **Relevance** (0-10): Does the response directly address the task?
3. **Completeness** (0-10): Does the response cover all aspects of the task?
4. **Instruction Following** (0-10): Does the response follow the format/constraints of the task?

## Output Format
Respond ONLY with a JSON object in this exact format:
{{
  "accuracy": <0-10>,
  "relevance": <0-10>,
  "completeness": <0-10>,
  "instruction_following": <0-10>,
  "overall": <0-10>,
  "reasoning": "<one sentence justification>"
}}
"""


@dataclass
class JudgeResult:
    overall: float              # 0.0–1.0 (normalized from 0-10)
    accuracy: float
    relevance: float
    completeness: float
    instruction_following: float
    reasoning: str
    judge_model_version: str
    raw_response: str


async def llm_judge_quality(
    task_prompt: str,
    response: str,
    reference: Optional[str],
    judge_adapter,           # BaseAdapter instance
    judge_model_id: str,
    judge_model_version: str,
) -> JudgeResult:
    """
    Score an open-ended response using LLM-as-a-Judge.
    Returns a JudgeResult with normalized scores (0–1).

    The judge_model_version is stored in every score for reproducibility (SRS FR-3.5).
    """
    import json

    prompt = _JUDGE_PROMPT_TEMPLATE.format(
        task_prompt=task_prompt,
        response=response,
        reference=reference or "(no reference answer provided — assess on general quality)",
    )

    result = await judge_adapter.call(
        model_id=judge_model_id,
        prompt=prompt,
        system_prompt="You are an objective, expert AI evaluator. Follow the output format exactly.",
        max_tokens=300,
        temperature=0.0,
    )

    from app.adapters.base import AdapterError
    if isinstance(result, AdapterError):
        # Return a neutral score on judge failure — do not propagate
        return JudgeResult(
            overall=0.5,
            accuracy=0.5,
            relevance=0.5,
            completeness=0.5,
            instruction_following=0.5,
            reasoning=f"Judge unavailable: {result.message}",
            judge_model_version=judge_model_version,
            raw_response="",
        )

    raw = result.text
    if isinstance(raw, dict):
        raw = json.dumps(raw)
    raw = str(raw).strip()

    # Extract JSON from response (model may wrap in markdown)
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        return JudgeResult(
            overall=0.5,
            accuracy=0.5,
            relevance=0.5,
            completeness=0.5,
            instruction_following=0.5,
            reasoning=f"Could not parse judge response: {raw[:100]}",
            judge_model_version=judge_model_version,
            raw_response=raw,
        )

    try:
        scores = json.loads(json_match.group())
        def norm(v: float) -> float:
            return max(0.0, min(1.0, float(v) / 10.0))

        return JudgeResult(
            overall=norm(scores.get("overall", 5)),
            accuracy=norm(scores.get("accuracy", 5)),
            relevance=norm(scores.get("relevance", 5)),
            completeness=norm(scores.get("completeness", 5)),
            instruction_following=norm(scores.get("instruction_following", 5)),
            reasoning=scores.get("reasoning", ""),
            judge_model_version=judge_model_version,
            raw_response=raw,
        )
    except (json.JSONDecodeError, ValueError):
        return JudgeResult(
            overall=0.5,
            accuracy=0.5,
            relevance=0.5,
            completeness=0.5,
            instruction_following=0.5,
            reasoning=f"JSON parse error in judge response.",
            judge_model_version=judge_model_version,
            raw_response=raw,
        )
