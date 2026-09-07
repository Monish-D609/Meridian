"""
Meridian API — Run Results endpoints.

Provides:
  GET /runs/{id}/results           — all results for a run
  GET /runs/{id}/results/{model_id} — per-model results with scores
  GET /results/{rr_id}/scores      — all evaluation scores for one RunResult
  GET /runs/{id}/comparison        — full comparison dashboard payload
  GET /runs/{id}/capability-profiles — radar chart data per model
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import BenchmarkRun, EvaluationScore, Model, RunResult

router = APIRouter()


class ScoreOut(BaseModel):
    id: str
    metric_name: str
    score: Optional[float]
    score_metadata: Optional[dict]
    scorer_version: str
    judge_model_version: Optional[str]
    model_config = {"from_attributes": True}


class RunResultOut(BaseModel):
    id: str
    run_id: str
    model_id: str
    task_id: str
    status: str
    response_text: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: Optional[int]
    error_message: Optional[str]
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
@router.get("/runs/{run_id}/results", response_model=list[RunResultOut])
async def list_run_results(
    run_id: str,
    model_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(RunResult).where(RunResult.run_id == run_id)
    if model_id:
        q = q.where(RunResult.model_id == model_id)
    if status:
        q = q.where(RunResult.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/results/{result_id}", response_model=RunResultOut)
async def get_run_result(result_id: str, db: AsyncSession = Depends(get_db)):
    rr = await db.get(RunResult, result_id)
    if not rr:
        raise HTTPException(status_code=404, detail="Run result not found")
    return rr


@router.get("/results/{result_id}/scores", response_model=list[ScoreOut])
async def get_result_scores(result_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvaluationScore).where(EvaluationScore.run_result_id == result_id)
    )
    return result.scalars().all()


@router.get("/runs/{run_id}/comparison")
async def get_run_comparison(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Full comparison dashboard payload for a completed run.
    Returns per-model summary: quality, hallucination, efficiency, cost,
    capability tiers, and positioning summary.
    """
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get all run results
    rr_result = await db.execute(
        select(RunResult).where(RunResult.run_id == run_id)
    )
    all_rrs = rr_result.scalars().all()

    # Get all scores for this run (grouped by model)
    from collections import defaultdict
    model_summaries = {}

    # Get unique model IDs
    model_ids = list({rr.model_id for rr in all_rrs})

    for model_id in model_ids:
        model = await db.get(Model, model_id)
        if not model:
            continue

        model_rrs = [rr for rr in all_rrs if rr.model_id == model_id]
        succeeded = [rr for rr in model_rrs if rr.status == "succeeded"]

        # Aggregate scores
        metric_values: dict[str, list[float]] = defaultdict(list)
        tier_breakdown: dict = {}
        positioning: dict = {}
        claim_metadata: list = []

        for rr in model_rrs:
            scores_result = await db.execute(
                select(EvaluationScore).where(EvaluationScore.run_result_id == rr.id)
            )
            scores = scores_result.scalars().all()
            for s in scores:
                if s.score is not None:
                    if s.metric_name.startswith("capability_tier_"):
                        cat = s.metric_name.replace("capability_tier_", "")
                        tier_breakdown[cat] = s.score_metadata or {}
                    elif s.metric_name == "positioning_summary":
                        positioning = s.score_metadata or {}
                    else:
                        metric_values[s.metric_name].append(s.score)

        # Average per metric
        avg_metrics = {
            k: round(sum(v) / len(v), 4) for k, v in metric_values.items() if v
        }

        model_summaries[model_id] = {
            "model_id": model_id,
            "model_display_name": model.display_name,
            "model_external_id": model.model_id_external,
            "total_tasks": len(model_rrs),
            "succeeded_tasks": len(succeeded),
            "failed_tasks": len(model_rrs) - len(succeeded),
            "avg_metrics": avg_metrics,
            "tier_breakdown": tier_breakdown,
            "positioning_summary": positioning,
        }

    return {
        "run_id": run_id,
        "run_name": run.name,
        "run_status": run.status,
        "judge_model": f"{run.judge_provider}/{run.judge_model_id}",
        "judge_model_version": run.judge_model_version,
        "models": list(model_summaries.values()),
        "config": run.config_json,
    }


@router.get("/runs/{run_id}/capability-profiles")
async def get_capability_profiles(run_id: str, db: AsyncSession = Depends(get_db)):
    """Radar chart data: per-model capability profile across all categories."""
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    rr_result = await db.execute(
        select(RunResult).where(RunResult.run_id == run_id)
    )
    all_rrs = rr_result.scalars().all()
    model_ids = list({rr.model_id for rr in all_rrs})

    profiles = []
    for model_id in model_ids:
        model = await db.get(Model, model_id)
        if not model:
            continue

        # Find positioning summary score (has the profile data)
        model_rrs = [rr for rr in all_rrs if rr.model_id == model_id]
        for rr in model_rrs:
            scores_result = await db.execute(
                select(EvaluationScore).where(
                    EvaluationScore.run_result_id == rr.id,
                    EvaluationScore.metric_name == "positioning_summary",
                )
            )
            ps = scores_result.scalar_one_or_none()
            if ps and ps.score_metadata:
                profiles.append({
                    "model_id": model_id,
                    "model_display_name": model.display_name,
                    **ps.score_metadata,
                })
                break

    return {"run_id": run_id, "profiles": profiles}
