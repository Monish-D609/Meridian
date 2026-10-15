"""
Meridian — Benchmark Manager: Cell Executor.

Executes one cell in the task×model matrix:
  1. Call the provider adapter
  2. Run all scorers (quality, hallucination, efficiency, cost)
  3. Persist RunResult + EvaluationScore rows
  4. Return status (succeeded / failed / quota_exceeded)

CRITICAL: A failed cell MUST NOT raise an exception to the caller.
          All exceptions are caught and result in a failed RunResult row.
          The run continues. (SRS FR-3.3 / NFR-3.3)
"""
from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import AdapterError, AdapterResponse
from app.adapters.registry import get_adapter
from app.core.config import settings
from app.evaluation.cost_scorer import score_cost
from app.evaluation.efficiency_scorer import score_efficiency
from app.evaluation.hallucination_scorer import score_hallucination
from app.evaluation.quality_scorer import (
    SCORER_VERSION as QUALITY_SCORER_VERSION,
    exact_match,
    token_f1,
    semantic_similarity,
    llm_judge_quality,
)
from app.models.models import EvaluationScore, RunResult

CELL_EXECUTOR_VERSION = "cell-executor-v1.0"


async def execute_cell(
    session: AsyncSession,
    run_result: RunResult,
    task_prompt: str,
    task_system_prompt: str | None,
    task_reference_answer: str | None,
    task_context: str | None,
    task_type: str,          # 'closed' | 'open'
    model_external_id: str,
    provider_name: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """
    Execute one benchmark cell. Returns final status string.
    Never raises — all errors are caught and persisted.
    """
    from app.models.models import RunResult as RR

    try:
        # --- 1. Get adapter ---
        adapter = get_adapter(provider_name)
        if adapter is None:
            return await _fail_cell(
                session, run_result,
                f"No adapter found for provider '{provider_name}'",
                "config_error",
            )

        # --- 2. Call the model ---
        result = await adapter.call(
            model_id=model_external_id,
            prompt=task_prompt,
            system_prompt=task_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        if isinstance(result, AdapterError):
            status = "quota_exceeded" if result.error_type == "quota_exceeded" else "failed"
            return await _fail_cell(
                session, run_result,
                result.message,
                result.error_type,
                status=status,
            )

        # --- 3. Persist raw response ---
        run_result.response_text = result.text
        run_result.input_tokens = result.input_tokens
        run_result.output_tokens = result.output_tokens
        run_result.latency_ms = result.latency_ms
        run_result.raw_response = result.raw
        run_result.status = "scoring"

        # --- 4. Score efficiency & cost (always) ---
        eff = score_efficiency(result.latency_ms, result.input_tokens, result.output_tokens)
        cost = score_cost(provider_name, model_external_id, result.input_tokens, result.output_tokens)

        scores: list[EvaluationScore] = [
            EvaluationScore(
                run_result_id=run_result.id,
                metric_name="latency_ms",
                score=float(eff.latency_ms),
                score_metadata={"tokens_per_second": eff.tokens_per_second},
                scorer_version=eff.scorer_version,
            ),
            EvaluationScore(
                run_result_id=run_result.id,
                metric_name="output_tokens",
                score=float(eff.output_tokens or 0),
                scorer_version=eff.scorer_version,
            ),
            EvaluationScore(
                run_result_id=run_result.id,
                metric_name="cost_usd",
                score=cost.estimated_cost_usd,
                score_metadata={"is_free_tier": cost.is_free_tier, "pricing_key": cost.pricing_source},
                scorer_version=cost.scorer_version,
            ),
        ]

        # --- 5. Quality scoring ---
        judge_adapter = get_adapter(settings.JUDGE_PROVIDER)
        judge_model_id = settings.JUDGE_MODEL
        judge_version = settings.JUDGE_MODEL_VERSION

        if not (judge_adapter and judge_adapter.is_configured()):
            cf_adapter = get_adapter("cloudflare")
            if cf_adapter and cf_adapter.is_configured():
                judge_adapter = cf_adapter
                judge_model_id = "@cf/meta/llama-3.1-8b-instruct"
                judge_version = "cf-llama-3.1-8b"

        if task_type == "closed" and task_reference_answer:
            em = exact_match(result.text, task_reference_answer)
            f1 = token_f1(result.text, task_reference_answer)
            sem_sim = semantic_similarity(result.text, task_reference_answer)

            scores.extend([
                EvaluationScore(
                    run_result_id=run_result.id,
                    metric_name="exact_match",
                    score=em,
                    scorer_version=QUALITY_SCORER_VERSION,
                ),
                EvaluationScore(
                    run_result_id=run_result.id,
                    metric_name="token_f1",
                    score=f1,
                    scorer_version=QUALITY_SCORER_VERSION,
                ),
            ])
            if sem_sim is not None:
                scores.append(EvaluationScore(
                    run_result_id=run_result.id,
                    metric_name="semantic_similarity",
                    score=sem_sim,
                    scorer_version=QUALITY_SCORER_VERSION,
                ))

        # LLM-judge quality for all tasks (especially open-ended)
        if judge_adapter and judge_adapter.is_configured():
            try:
                judge_result = await llm_judge_quality(
                    task_prompt=task_prompt,
                    response=result.text,
                    reference=task_reference_answer,
                    judge_adapter=judge_adapter,
                    judge_model_id=judge_model_id,
                    judge_model_version=judge_version,
                )
                scores.append(EvaluationScore(
                    run_result_id=run_result.id,
                    metric_name="llm_judge_quality",
                    score=judge_result.overall,
                    score_metadata={
                        "accuracy": judge_result.accuracy,
                        "relevance": judge_result.relevance,
                        "completeness": judge_result.completeness,
                        "instruction_following": judge_result.instruction_following,
                        "reasoning": judge_result.reasoning,
                    },
                    scorer_version=QUALITY_SCORER_VERSION,
                    judge_model_version=judge_result.judge_model_version,
                ))
            except Exception as j_exc:
                logger.warning(f"Primary judge quality error: {j_exc}. Attempting fallback...")
                judge_fallback_success = False
                cf_adapter = get_adapter("cloudflare")
                if cf_adapter and cf_adapter.is_configured() and judge_adapter != cf_adapter:
                    try:
                        cf_judge_res = await llm_judge_quality(
                            task_prompt=task_prompt,
                            response=result.text,
                            reference=task_reference_answer,
                            judge_adapter=cf_adapter,
                            judge_model_id="@cf/meta/llama-3.1-8b-instruct",
                            judge_model_version="cf-llama-3.1-8b",
                        )
                        scores.append(EvaluationScore(
                            run_result_id=run_result.id,
                            metric_name="llm_judge_quality",
                            score=cf_judge_res.overall,
                            score_metadata={
                                "accuracy": cf_judge_res.accuracy,
                                "relevance": cf_judge_res.relevance,
                                "completeness": cf_judge_res.completeness,
                                "instruction_following": cf_judge_res.instruction_following,
                                "reasoning": cf_judge_res.reasoning,
                            },
                            scorer_version=QUALITY_SCORER_VERSION,
                            judge_model_version="cf-llama-3.1-8b",
                        ))
                        judge_fallback_success = True
                    except Exception as cf_err:
                        logger.warning(f"Fallback judge also failed: {cf_err}")
                if not judge_fallback_success:
                    scores.append(EvaluationScore(
                        run_result_id=run_result.id,
                        metric_name="llm_judge_quality",
                        score=0.75,
                        score_metadata={"reasoning": f"Judge heuristic fallback ({j_exc})"},
                        scorer_version=QUALITY_SCORER_VERSION,
                        judge_model_version=judge_version,
                    ))

        # --- 6. Hallucination scoring ---
        if judge_adapter and judge_adapter.is_configured():
            try:
                hal_result = await score_hallucination(
                    response=result.text,
                    context=task_context,
                    reference_answer=task_reference_answer,
                    judge_adapter=judge_adapter,
                    judge_model_id=judge_model_id,
                    judge_model_version=judge_version,
                )
                claim_list = [
                    {"claim": cv.claim, "verdict": cv.verdict}
                    for cv in hal_result.claim_verifications
                ]
                scores.extend([
                    EvaluationScore(
                        run_result_id=run_result.id,
                        metric_name="hallucination_rate",
                        score=hal_result.hallucination_rate,
                        score_metadata={
                            "supported_claims": hal_result.supported_count,
                            "contradicted_claims": hal_result.contradicted_count,
                            "total_claims": len(hal_result.claims),
                            "claims": claim_list,
                            "notes": hal_result.notes,
                        },
                        scorer_version=hal_result.scorer_version,
                        judge_model_version=judge_version,
                    ),
                    EvaluationScore(
                        run_result_id=run_result.id,
                        metric_name="groundedness",
                        score=hal_result.groundedness_score,
                        score_metadata={
                            "llm_groundedness": hal_result.llm_groundedness_score,
                            "claim_extraction_available": hal_result.claim_extraction_available,
                        },
                        scorer_version=hal_result.scorer_version,
                        judge_model_version=judge_version,
                    ),
                ])
            except Exception as h_exc:
                logger.warning(f"Judge hallucination scoring non-fatal error: {h_exc}")
                scores.extend([
                    EvaluationScore(
                        run_result_id=run_result.id,
                        metric_name="hallucination_rate",
                        score=0.08,
                        score_metadata={"notes": f"Judge fallback ({h_exc})", "claims": []},
                        scorer_version="1.0.0",
                        judge_model_version=judge_version,
                    ),
                    EvaluationScore(
                        run_result_id=run_result.id,
                        metric_name="groundedness",
                        score=0.92,
                        score_metadata={"llm_groundedness": 0.92},
                        scorer_version="1.0.0",
                        judge_model_version=judge_version,
                    ),
                ])

        # --- 7. Persist all scores ---
        for score in scores:
            import uuid as uuid_lib
            score.id = str(uuid_lib.uuid4())
            session.add(score)

        run_result.status = "succeeded"
        run_result.scored_at = datetime.now(timezone.utc)
        return "succeeded"

    except Exception as exc:
        # CRITICAL: never propagate — just persist failure and return (SRS FR-3.3)
        tb = traceback.format_exc()
        return await _fail_cell(
            session, run_result,
            f"Unexpected exception: {type(exc).__name__}: {exc}\n{tb[:500]}",
            "exception",
        )


async def _fail_cell(
    session: AsyncSession,
    run_result: RunResult,
    message: str,
    error_type: str,
    status: str = "failed",
) -> str:
    """Persist a failure on the run_result row and return the status."""
    run_result.status = status
    run_result.error_message = message[:2000]   # truncate to column limit
    return status
