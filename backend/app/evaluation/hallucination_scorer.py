"""
Meridian — Hallucination & Reliability Scorer.

Implements claim-level hallucination detection as a first-class metric (SRS FR-5.x).
This is one of Meridian's core novelties vs. existing tools.

Pipeline:
  1. Claim extraction: decompose the response into atomic factual claims (via LLM)
  2. Claim verification: verify each claim against the reference/context (via LLM)
  3. Groundedness score: fraction of claims supported by the source
  4. Consistency score: semantic similarity across repeated samples (if available)

Methodology adapted from RAGAS faithfulness concept (Apache 2.0, concept only, not code).
Attribution: RAGAS https://github.com/explodinggradients/ragas
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

SCORER_VERSION = "hallucination-scorer-v1.0"

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_CLAIM_EXTRACTION_PROMPT = """\
Given the following AI-generated response, extract all atomic factual claims.
A claim is a single, verifiable factual statement that can be independently checked.
Ignore opinions, hedges, and procedural statements. Focus on factual assertions.

Response:
{response}

Output ONLY a JSON array of strings, each being one atomic claim:
["claim 1", "claim 2", ...]
"""

_CLAIM_VERIFICATION_PROMPT = """\
You are a fact-checker. Given a claim and a reference source, determine if the claim is supported.

Reference Source:
{context}

Claim to verify:
{claim}

Answer ONLY with one of:
- "supported" — the claim is directly supported by the reference
- "contradicted" — the claim contradicts the reference
- "insufficient_info" — the reference doesn't have enough information to verify

Your answer:
"""

_GROUNDEDNESS_PROMPT = """\
Given the following AI response and its source context, assess how grounded the response is.
Grounded means the response only states things that are supported by or can be inferred from the context.

Context:
{context}

Response:
{response}

Rate the overall groundedness on a scale of 0 to 10 (10 = fully grounded, 0 = completely ungrounded).
Respond ONLY with a JSON object:
{{"groundedness_score": <0-10>, "reasoning": "<one sentence>"}}
"""


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ClaimVerification:
    claim: str
    verdict: str       # 'supported' | 'contradicted' | 'insufficient_info'


@dataclass
class HallucinationResult:
    """
    Comprehensive hallucination and reliability scores for one RunResult.
    All scores are [0, 1] where higher = better (less hallucination).
    """
    # Claim-level
    claims: list[str] = field(default_factory=list)
    claim_verifications: list[ClaimVerification] = field(default_factory=list)
    supported_count: int = 0
    contradicted_count: int = 0
    insufficient_count: int = 0

    # Derived scores [0, 1]
    groundedness_score: float = 0.5       # fraction of claims supported
    hallucination_rate: float = 0.5       # fraction of claims contradicted
    faithfulness_score: float = 0.5       # 1 - hallucination_rate (alias)
    llm_groundedness_score: Optional[float] = None  # holistic LLM-rated groundedness

    # Consistency (multi-sample)
    consistency_score: Optional[float] = None   # semantic similarity across repeated samples

    # Metadata
    scorer_version: str = SCORER_VERSION
    judge_model_version: str = ""
    claim_extraction_available: bool = False
    notes: str = ""


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

async def extract_claims(
    response: str,
    judge_adapter,
    judge_model_id: str,
) -> list[str]:
    """
    Use the LLM judge to extract atomic factual claims from a response.
    Returns an empty list if extraction fails (graceful degradation).
    """
    from app.adapters.base import AdapterError

    prompt = _CLAIM_EXTRACTION_PROMPT.format(response=response)
    result = await judge_adapter.call(
        model_id=judge_model_id,
        prompt=prompt,
        system_prompt="You are an expert fact-checker. Follow the output format exactly.",
        max_tokens=500,
        temperature=0.0,
    )

    if isinstance(result, AdapterError):
        return []

    raw = result.text
    if isinstance(raw, dict):
        raw = json.dumps(raw)
    raw = str(raw).strip()
    # Find JSON array in response
    json_match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if not json_match:
        return []

    try:
        claims = json.loads(json_match.group())
        return [c for c in claims if isinstance(c, str) and c.strip()]
    except (json.JSONDecodeError, ValueError):
        return []


# ---------------------------------------------------------------------------
# Claim verification
# ---------------------------------------------------------------------------

async def verify_claim(
    claim: str,
    context: str,
    judge_adapter,
    judge_model_id: str,
) -> ClaimVerification:
    """Verify one claim against the reference context."""
    from app.adapters.base import AdapterError

    prompt = _CLAIM_VERIFICATION_PROMPT.format(context=context, claim=claim)
    result = await judge_adapter.call(
        model_id=judge_model_id,
        prompt=prompt,
        system_prompt="You are an expert fact-checker. Answer with exactly one word from the given options.",
        max_tokens=20,
        temperature=0.0,
    )

    if isinstance(result, AdapterError):
        return ClaimVerification(claim=claim, verdict="insufficient_info")

    raw = result.text
    if isinstance(raw, dict):
        raw = json.dumps(raw)
    raw = str(raw).strip().lower()
    if "contradicted" in raw:
        verdict = "contradicted"
    elif "supported" in raw:
        verdict = "supported"
    else:
        verdict = "insufficient_info"

    return ClaimVerification(claim=claim, verdict=verdict)


# ---------------------------------------------------------------------------
# Holistic groundedness scoring
# ---------------------------------------------------------------------------

async def score_groundedness_holistic(
    response: str,
    context: str,
    judge_adapter,
    judge_model_id: str,
    judge_model_version: str,
) -> Optional[float]:
    """Score overall groundedness [0, 1] via LLM judge when claim-level is unavailable."""
    from app.adapters.base import AdapterError

    prompt = _GROUNDEDNESS_PROMPT.format(context=context, response=response)
    result = await judge_adapter.call(
        model_id=judge_model_id,
        prompt=prompt,
        system_prompt="You are an expert fact-checker.",
        max_tokens=100,
        temperature=0.0,
    )

    if isinstance(result, AdapterError):
        return None

    raw = result.text
    if isinstance(raw, dict):
        raw = json.dumps(raw)
    raw = str(raw).strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        return None

    try:
        data = json.loads(json_match.group())
        score = float(data.get("groundedness_score", 5))
        return max(0.0, min(1.0, score / 10.0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Main scorer function
# ---------------------------------------------------------------------------

async def score_hallucination(
    response: str,
    context: Optional[str],            # grounding source / reference passage
    reference_answer: Optional[str],   # gold answer (used as fallback context)
    judge_adapter,
    judge_model_id: str,
    judge_model_version: str,
    attempt_claim_level: bool = True,  # set False to skip to holistic if context is too long
) -> HallucinationResult:
    """
    Full hallucination and reliability scoring pipeline.

    If context is available:
      - Attempt claim-level extraction + verification
      - Also compute holistic groundedness score
    If no context:
      - Use reference_answer as a proxy context
      - Fall back to holistic score only
    """
    result = HallucinationResult(
        scorer_version=SCORER_VERSION,
        judge_model_version=judge_model_version,
    )

    grounding_source = context or reference_answer
    if not grounding_source:
        result.notes = "No context or reference available for hallucination scoring."
        result.groundedness_score = 0.5
        result.hallucination_rate = 0.5
        result.faithfulness_score = 0.5
        return result

    # --- Holistic groundedness ---
    holistic = await score_groundedness_holistic(
        response=response,
        context=grounding_source,
        judge_adapter=judge_adapter,
        judge_model_id=judge_model_id,
        judge_model_version=judge_model_version,
    )
    result.llm_groundedness_score = holistic

    # --- Claim-level (when context is available and not too long) ---
    if attempt_claim_level and len(grounding_source) < 8000:
        claims = await extract_claims(
            response=response,
            judge_adapter=judge_adapter,
            judge_model_id=judge_model_id,
        )
        result.claims = claims
        result.claim_extraction_available = len(claims) > 0

        if claims:
            verifications: list[ClaimVerification] = []
            for claim in claims[:3]:   # cap at 3 claims to stay within free-tier rate limits
                cv = await verify_claim(
                    claim=claim,
                    context=grounding_source,
                    judge_adapter=judge_adapter,
                    judge_model_id=judge_model_id,
                )
                verifications.append(cv)

            result.claim_verifications = verifications
            total = len(verifications)
            result.supported_count = sum(1 for v in verifications if v.verdict == "supported")
            result.contradicted_count = sum(1 for v in verifications if v.verdict == "contradicted")
            result.insufficient_count = sum(1 for v in verifications if v.verdict == "insufficient_info")

            if total > 0:
                result.groundedness_score = result.supported_count / total
                result.hallucination_rate = result.contradicted_count / total
                result.faithfulness_score = 1.0 - result.hallucination_rate
            else:
                # Fallback to holistic
                result.groundedness_score = holistic if holistic is not None else 0.5
                result.faithfulness_score = holistic if holistic is not None else 0.5
                result.hallucination_rate = 1.0 - result.groundedness_score
        else:
            # Claim extraction failed — use holistic score
            result.groundedness_score = holistic if holistic is not None else 0.5
            result.faithfulness_score = holistic if holistic is not None else 0.5
            result.hallucination_rate = 1.0 - result.groundedness_score
            result.notes = "Claim extraction returned no claims; using holistic groundedness score."
    else:
        # No claim-level: use holistic
        result.groundedness_score = holistic if holistic is not None else 0.5
        result.faithfulness_score = holistic if holistic is not None else 0.5
        result.hallucination_rate = 1.0 - result.groundedness_score

    return result


# ---------------------------------------------------------------------------
# Consistency scoring (multi-sample)
# ---------------------------------------------------------------------------

def score_consistency(responses: list[str]) -> Optional[float]:
    """
    Compute consistency as the average pairwise semantic similarity
    across repeated samples of the same prompt.
    Returns None if fewer than 2 samples or embeddings unavailable.
    """
    if len(responses) < 2:
        return None

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        import numpy as np  # type: ignore

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(responses, convert_to_numpy=True)

        sims = []
        n = len(embeddings)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = embeddings[i], embeddings[j]
                cosine = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
                sims.append(max(0.0, min(1.0, cosine)))

        return float(sum(sims) / len(sims)) if sims else None
    except ImportError:
        return None
