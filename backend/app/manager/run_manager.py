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
    task_mix_mode: str = "standard",
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
    tasks: list[Task] = []
    if task_mix_mode == "quick":
        for ds_id in dataset_ids:
            t_res = await session.execute(
                select(Task).where(Task.dataset_id == ds_id).order_by(Task.created_at).limit(2)
            )
            tasks.extend(t_res.scalars().all())
    else:
        tasks_result = await session.execute(
            select(Task).where(Task.dataset_id.in_(dataset_ids)).order_by(Task.created_at)
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

    try:
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

        _db_write_lock = asyncio.Lock()

        # Execute cells concurrently with semaphore
        async def _execute_one(cell_id: str) -> tuple[str, str]:
            """Execute one cell in its own session. Returns (cell_id, status)."""
            async with semaphore:
                try:
                    async with session_factory() as cell_session:
                        cell = await cell_session.get(RunResult, cell_id)
                        if cell is None:
                            return cell_id, "failed"

                        # Load task and model details
                        task = await cell_session.get(Task, cell.task_id)
                        model = await cell_session.get(Model, cell.model_id)

                        if task is None or model is None:
                            async with _db_write_lock:
                                cell.status = "failed"
                                cell.error_message = "Task or model not found."
                                await cell_session.commit()
                            return cell_id, "failed"

                        # Load dataset for task_type
                        dataset = await cell_session.get(Dataset, task.dataset_id)
                        task_type = dataset.task_type if dataset else "open"

                        # Load provider name safely without touching lazy relationships
                        from app.models.models import Provider
                        provider_obj = await cell_session.get(Provider, model.provider_id)
                        p_lower = provider_obj.name.lower() if provider_obj else "unknown"

                        if "cloudflare" in p_lower:
                            adapter_key = "cloudflare"
                        elif "gemini" in p_lower or "google" in p_lower:
                            adapter_key = "gemini"
                        elif "grok" in p_lower or "xai" in p_lower:
                            adapter_key = "xai"
                        elif "groq" in p_lower:
                            adapter_key = "groq"
                        elif "openrouter" in p_lower:
                            adapter_key = "openrouter"
                        elif "nvidia" in p_lower or "nim" in p_lower:
                            adapter_key = "nvidia_nim"
                        else:
                            adapter_key = p_lower.replace(" ", "_")

                        async with _db_write_lock:
                            cell.status = "running"
                            await cell_session.commit()

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
                        async with _db_write_lock:
                            await cell_session.commit()
                        return cell_id, status
                except Exception as exc:
                    import traceback
                    print(f"[ERROR] Cell {cell_id} execution failed: {type(exc).__name__}: {exc}")
                    traceback.print_exc()
                    try:
                        async with _db_write_lock:
                            async with session_factory() as err_session:
                                c = await err_session.get(RunResult, cell_id)
                                if c:
                                    c.status = "failed"
                                    c.error_message = f"{type(exc).__name__}: {exc}"
                                    await err_session.commit()
                    except Exception:
                        pass
                    return cell_id, "failed"

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
        try:
            async with session_factory() as session:
                await _run_industry_comparison(run_id=run_id, session=session)
        except Exception as comp_exc:
            print(f"[WARN] Industry comparison error: {comp_exc}")

        async with session_factory() as session:
            return await session.get(BenchmarkRun, run_id)
    except Exception as run_exc:
        print(f"[FATAL] execute_run encountered unhandled exception: {run_exc}")
        try:
            async with session_factory() as session:
                run = await session.get(BenchmarkRun, run_id)
                if run:
                    run.status = "failed"
                    await session.commit()
        except Exception:
            pass
        raise


async def get_run_progress(run_id: str, session: AsyncSession) -> dict:
    """Return current progress stats for a run (for polling endpoint)."""
    from sqlalchemy import func, select

    run = await session.get(BenchmarkRun, run_id)
    run_status = run.status if run else "pending"

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
    succeeded_cells = status_counts.get("succeeded", 0)
    failed_cells = status_counts.get("failed", 0) + status_counts.get("quota_exceeded", 0)
    done = succeeded_cells + failed_cells

    # Also load brief cell objects so frontend progress tables can render live cells
    cell_query = await session.execute(
        select(RunResult.id, RunResult.model_id, RunResult.task_id, RunResult.status, RunResult.latency_ms, RunResult.error_message)
        .where(RunResult.run_id == run_id)
    )
    cells = [
        {
            "id": r.id,
            "model_id": r.model_id,
            "task_id": r.task_id,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "error_message": r.error_message,
        }
        for r in cell_query.all()
    ]

    return {
        "run_id": run_id,
        "status": run_status,
        "run_status": run_status,
        "total_cells": total,
        "done_cells": done,
        "succeeded_cells": succeeded_cells,
        "failed_cells": failed_cells,
        "succeeded": succeeded_cells,
        "failed": failed_cells,
        "pending": status_counts.get("pending", 0),
        "running": status_counts.get("running", 0),
        "progress_pct": round(done / total * 100, 1) if total > 0 else 0,
        "cells": cells,
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

    await session.commit()
