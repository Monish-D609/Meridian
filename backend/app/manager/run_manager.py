"""
Meridian — Benchmark Manager: Run Manager.

Orchestrates a full benchmark run:
  1. Validate run config (models, datasets, tasks)
  2. Build the task×model matrix
  3. Create RunResult rows (status=pending) for every cell
  4. Dispatch cells asynchronously with concurrency control
  5. Update BenchmarkRun status throughout
  6. Never abort on cell failure (SRS FR-3.3)

After all cells complete, triggers the Industry Comparison Engine to
compute capability profiles and positioning summaries.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.manager.cell_executor import execute_cell
from app.models.models import (
    BenchmarkRun,
    Dataset,
    Model,
    RunResult,
    Task,
)

# Max concurrent adapter calls (respect free-tier rate limits)
_MAX_CONCURRENT_CELLS = 3


async def create_run(
    session: AsyncSession,
    name: str,
    model_ids: list[str],          # internal UUIDs
    dataset_ids: list[str],        # internal UUIDs
    description: str = "",
    max_tokens: int = 1024,
    temperature: float = 0.0,
    config_overrides: Optional[dict] = None,
) -> BenchmarkRun:
    """
    Create a new BenchmarkRun and all its pending RunResult cells.
    Does NOT start execution — call execute_run() for that.
    """
    # Load models
    models_result = await session.execute(
        select(Model).where(Model.id.in_(model_ids), Model.is_active == True)
    )
    models = models_result.scalars().all()
    if not models:
        raise ValueError("No active models found for the given model_ids.")

    # Load datasets + their tasks
    tasks_result = await session.execute(
        select(Task).where(Task.dataset_id.in_(dataset_ids))
    )
    tasks = tasks_result.scalars().all()
    if not tasks:
        raise ValueError("No tasks found for the given dataset_ids.")

    config = {
        "model_ids": model_ids,
        "dataset_ids": dataset_ids,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "judge_provider": settings.JUDGE_PROVIDER,
        "judge_model": settings.JUDGE_MODEL,
        "judge_model_version": settings.JUDGE_MODEL_VERSION,
        "tier_thresholds": {
            "frontier": settings.TIER_FRONTIER_THRESHOLD,
            "strong": settings.TIER_STRONG_THRESHOLD,
            "mid": settings.TIER_MID_THRESHOLD,
        },
        **(config_overrides or {}),
    }

    run = BenchmarkRun(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        status="pending",
        config_json=config,
        judge_provider=settings.JUDGE_PROVIDER,
        judge_model_id=settings.JUDGE_MODEL,
        judge_model_version=settings.JUDGE_MODEL_VERSION,
        created_at=datetime.now(timezone.utc),
        total_cells=len(models) * len(tasks),
        succeeded_cells=0,
        failed_cells=0,
    )
    session.add(run)
    await session.flush()

    # Create RunResult rows for every (model, task) pair
    for model in models:
        for task in tasks:
            rr = RunResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                model_id=model.id,
                task_id=task.id,
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            session.add(rr)

    await session.commit()
    return run


async def execute_run(
    run_id: str,
    session_factory,          # AsyncSessionLocal callable
) -> BenchmarkRun:
    """
    Execute all pending cells for a BenchmarkRun.
    Uses a semaphore to cap concurrency at _MAX_CONCURRENT_CELLS.
    Updates run status to 'running' → 'completed'.
    """
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_CELLS)

    async with session_factory() as session:
        # Load run
        run = await session.get(BenchmarkRun, run_id)
        if run is None:
            raise ValueError(f"BenchmarkRun {run_id} not found.")
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await session.commit()

    # Load all pending cells
    async with session_factory() as session:
        rr_result = await session.execute(
            select(RunResult)
            .where(RunResult.run_id == run_id, RunResult.status == "pending")
        )
        pending_cells = rr_result.scalars().all()

    # Execute cells concurrently with semaphore
    async def _execute_one(cell_id: str) -> tuple[str, str]:
        """Execute one cell in its own session. Returns (cell_id, status)."""
        async with semaphore:
            async with session_factory() as cell_session:
                cell = await cell_session.get(RunResult, cell_id)
                if cell is None:
                    return cell_id, "failed"

                # Load task and model details
                task = await cell_session.get(Task, cell.task_id)
                model = await cell_session.get(Model, cell.model_id)

                if task is None or model is None:
                    cell.status = "failed"
                    cell.error_message = "Task or model not found."
                    await cell_session.commit()
                    return cell_id, "failed"

                # Load dataset for task_type
                dataset = await cell_session.get(Dataset, task.dataset_id)
                task_type = dataset.task_type if dataset else "open"

                # Load provider name
                from app.models.models import Provider
                provider = await cell_session.get(model.provider.__class__, model.provider_id)

                # We need the provider name — load it
                from sqlalchemy import select as sa_select
                from app.models.models import Provider as ProviderModel
                prov_result = await cell_session.execute(
                    sa_select(ProviderModel).where(ProviderModel.id == model.provider_id)
                )
                provider_obj = prov_result.scalar_one_or_none()
                provider_name = provider_obj.name.lower().replace(" ", "_") if provider_obj else "unknown"

                # Map provider display name to adapter key
                _PROVIDER_NAME_MAP = {
                    "groq": "groq",
                    "google_ai_studio": "gemini",
                    "google": "gemini",
                    "openrouter": "openrouter",
                    "cloudflare_workers_ai": "cloudflare",
                    "cloudflare": "cloudflare",
                    "nvidia_nim": "nvidia_nim",
                }
                adapter_key = _PROVIDER_NAME_MAP.get(provider_name, provider_name)

                cell.status = "running"
                await cell_session.flush()

                status = await execute_cell(
                    session=cell_session,
                    run_result=cell,
                    task_prompt=task.prompt,
                    task_system_prompt=task.system_prompt,
                    task_reference_answer=task.reference_answer,
                    task_context=task.context,
                    task_type=task_type,
                    model_external_id=model.model_id_external,
                    provider_name=adapter_key,
                )
                await cell_session.commit()
                return cell_id, status

    tasks_coros = [_execute_one(cell.id) for cell in pending_cells]
    results = await asyncio.gather(*tasks_coros, return_exceptions=True)

    # Tally results and update run
    succeeded = sum(1 for r in results if not isinstance(r, Exception) and r[1] == "succeeded")
    failed = sum(1 for r in results if isinstance(r, Exception) or r[1] != "succeeded")

    async with session_factory() as session:
        run = await session.get(BenchmarkRun, run_id)
        run.succeeded_cells = succeeded
        run.failed_cells = failed
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        await session.commit()

    # Trigger Industry Comparison Engine
    async with session_factory() as session:
        await _run_industry_comparison(run_id=run_id, session=session)

    async with session_factory() as session:
        return await session.get(BenchmarkRun, run_id)


async def get_run_progress(run_id: str, session: AsyncSession) -> dict:
    """Return current progress stats for a run (for polling endpoint)."""
    from sqlalchemy import func, select

    result = await session.execute(
        select(
            RunResult.status,
            func.count(RunResult.id).label("count"),
        )
        .where(RunResult.run_id == run_id)
        .group_by(RunResult.status)
    )
    rows = result.all()
    status_counts = {row.status: row.count for row in rows}
    total = sum(status_counts.values())
    done = status_counts.get("succeeded", 0) + status_counts.get("failed", 0) + status_counts.get("quota_exceeded", 0)
    return {
        "run_id": run_id,
        "total_cells": total,
        "done_cells": done,
        "succeeded": status_counts.get("succeeded", 0),
        "failed": status_counts.get("failed", 0),
        "pending": status_counts.get("pending", 0),
        "running": status_counts.get("running", 0),
        "progress_pct": round(done / total * 100, 1) if total > 0 else 0,
    }


async def _run_industry_comparison(run_id: str, session: AsyncSession) -> None:
    """
    Post-run step: compute normalized scores, tiers, capability profiles,
    and positioning summaries for each model in the run.
    Stores results as EvaluationScore rows with metric_name='capability_tier'.
    """
    from sqlalchemy import select as sa_select

    from app.comparison.normalizer import normalize_scores_batch
    from app.comparison.tier_classifier import classify_tiers_batch
    from app.comparison.capability_profile import build_capability_profile
    from app.comparison.summary_generator import generate_positioning_summary
    from app.models.models import (
        BaselineModel, BaselineScore, CapabilityCategory,
        EvaluationScore, Model,
    )

    import uuid as uuid_lib

    # --- Load run config ---
    run = await session.get(BenchmarkRun, run_id)
    if run is None:
        return

    # --- Load all run results for this run ---
    rr_result = await session.execute(
        sa_select(RunResult).where(
            RunResult.run_id == run_id,
            RunResult.status == "succeeded",
        )
    )
    run_results = rr_result.scalars().all()
    if not run_results:
        return

    # --- Load capability categories ---
    cats_result = await session.execute(sa_select(CapabilityCategory))
    categories = {cat.slug: cat for cat in cats_result.scalars().all()}

    # --- Load baseline scores ---
    baseline_scores_result = await session.execute(
        sa_select(BaselineScore)
    )
    all_baseline_scores = baseline_scores_result.scalars().all()

    # Build baseline distribution per category_slug → [scores]
    from app.models.models import CapabilityCategory as CC
    cat_id_to_slug = {cat.id: cat.slug for cat in categories.values()}
    baseline_by_category: dict[str, list[float]] = {slug: [] for slug in categories}
    for bs in all_baseline_scores:
        slug = cat_id_to_slug.get(bs.category_id)
        if slug:
            baseline_by_category[slug].append(bs.raw_score)

    # Check if baselines are placeholder
    bm_result = await session.execute(sa_select(BaselineModel).limit(1))
    first_bm = bm_result.scalar_one_or_none()
    is_placeholder = first_bm.is_placeholder if first_bm else True
    captured_date = first_bm.captured_date if first_bm else "unknown"

    # --- Group run_results by model ---
    from collections import defaultdict
    by_model: dict[str, list[RunResult]] = defaultdict(list)
    for rr in run_results:
        by_model[rr.model_id].append(rr)

    # --- Compute per-model quality score per category ---
    # (average llm_judge_quality score across tasks in each category's datasets)
    for model_id, model_rrs in by_model.items():
        model = await session.get(Model, model_id)
        if model is None:
            continue

        # For each RunResult, find its category via task → dataset → category
        cat_scores: dict[str, list[float]] = defaultdict(list)
        for rr in model_rrs:
            task = await session.get(Task, rr.task_id)
            if task is None:
                continue
            dataset = await session.get(Dataset, task.dataset_id)
            if dataset is None:
                continue
            cat = categories.get(cat_id_to_slug.get(dataset.category_id, ""), None)
            if cat is None:
                continue

            # Find the llm_judge_quality score for this run result
            scores_result = await session.execute(
                sa_select(EvaluationScore).where(
                    EvaluationScore.run_result_id == rr.id,
                    EvaluationScore.metric_name == "llm_judge_quality",
                )
            )
            judge_score = scores_result.scalar_one_or_none()
            if judge_score and judge_score.score is not None:
                cat_scores[cat.slug].append(judge_score.score)

        if not cat_scores:
            continue

        # Average score per category
        raw_scores_per_cat = {slug: sum(v) / len(v) for slug, v in cat_scores.items()}

        # Normalize and tier
        normalized = normalize_scores_batch(
            candidate_scores=raw_scores_per_cat,
            baseline_by_category=baseline_by_category,
            is_placeholder_baseline=is_placeholder,
        )
        tiers = classify_tiers_batch(normalized)

        # Persist tier scores
        for slug, tier_result in tiers.items():
            es = EvaluationScore(
                id=str(uuid_lib.uuid4()),
                run_result_id=model_rrs[0].id,   # attach to first result as summary row
                metric_name=f"capability_tier_{slug}",
                score=tier_result.percentile,
                score_metadata={
                    "tier": tier_result.tier.value,
                    "z_score": tier_result.z_score,
                    "raw_score": raw_scores_per_cat.get(slug),
                    "baseline_count": tier_result.baseline_count,
                    "is_placeholder_baseline": is_placeholder,
                    "baseline_captured_date": captured_date,
                },
                scorer_version="industry-comparison-engine-v1.0",
            )
            session.add(es)

        # Build capability profile + positioning summary
        profile = build_capability_profile(
            model_id=model_id,
            model_display_name=model.display_name,
            run_id=run_id,
            raw_scores=raw_scores_per_cat,
            normalized_scores=normalized,
            tiers=tiers,
            baseline_captured_date=captured_date,
            is_placeholder_baseline=is_placeholder,
        )

        summary = generate_positioning_summary(profile=profile, model_display_name=model.display_name)

        # Persist positioning summary as a JSON score
        es_summary = EvaluationScore(
            id=str(uuid_lib.uuid4()),
            run_result_id=model_rrs[0].id,
            metric_name="positioning_summary",
            score=profile.mean_raw_score,
            score_metadata={
                "headline": summary.headline,
                "narrative": summary.narrative,
                "tier_breakdown": summary.tier_breakdown,
                "strongest": summary.strongest_strengths,
                "weaknesses": summary.key_weaknesses,
                "baseline_disclaimer": summary.baseline_disclaimer,
                "generated_at": summary.generated_at,
                "overall_tier": profile.overall_tier,
            },
            scorer_version="industry-comparison-engine-v1.0",
        )
        session.add(es_summary)

    await session.flush()
