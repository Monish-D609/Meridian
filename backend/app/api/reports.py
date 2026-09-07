"""
Meridian API — Reports endpoints.

Generates PDF and CSV exports of benchmark run results.
SRS FR-8.x — Reporting & Visualization.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import BenchmarkRun, EvaluationScore, Model, Report, RunResult

router = APIRouter()


@router.get("/runs/{run_id}/report/csv")
async def download_csv_report(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Export a benchmark run's results as CSV.
    Each row: model, task, metric_name, score.
    """
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in ("completed", "failed"):
        raise HTTPException(status_code=409, detail="Run not yet complete")

    # Collect all run results + scores
    rr_result = await db.execute(
        select(RunResult).where(RunResult.run_id == run_id)
    )
    all_rrs = rr_result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "run_id", "run_name", "model_id", "model_name",
        "task_id", "status", "latency_ms",
        "metric_name", "score", "scorer_version", "judge_model_version",
        "baseline_captured_date",
    ])

    for rr in all_rrs:
        model = await db.get(Model, rr.model_id)
        model_name = model.display_name if model else rr.model_id

        scores_result = await db.execute(
            select(EvaluationScore).where(EvaluationScore.run_result_id == rr.id)
        )
        scores = scores_result.scalars().all()

        if not scores:
            writer.writerow([
                run_id, run.name, rr.model_id, model_name,
                rr.task_id, rr.status, rr.latency_ms,
                "N/A", "N/A", "N/A", "N/A", "N/A",
            ])
        else:
            for s in scores:
                meta = s.score_metadata or {}
                baseline_date = meta.get("baseline_captured_date", "")
                writer.writerow([
                    run_id, run.name, rr.model_id, model_name,
                    rr.task_id, rr.status, rr.latency_ms,
                    s.metric_name, s.score, s.scorer_version,
                    s.judge_model_version or "", baseline_date,
                ])

    output.seek(0)
    filename = f"meridian_run_{run_id[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/runs/{run_id}/report/json")
async def download_json_report(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Export a complete run report as JSON (machine-readable, reproducibility).
    Includes full config, all scores, baseline metadata, judge identity.
    """
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    rr_result = await db.execute(
        select(RunResult).where(RunResult.run_id == run_id)
    )
    all_rrs = rr_result.scalars().all()

    results_payload = []
    for rr in all_rrs:
        model = await db.get(Model, rr.model_id)
        scores_result = await db.execute(
            select(EvaluationScore).where(EvaluationScore.run_result_id == rr.id)
        )
        scores = scores_result.scalars().all()

        results_payload.append({
            "run_result_id": rr.id,
            "model_id": rr.model_id,
            "model_display_name": model.display_name if model else None,
            "task_id": rr.task_id,
            "status": rr.status,
            "response_text": rr.response_text,
            "latency_ms": rr.latency_ms,
            "input_tokens": rr.input_tokens,
            "output_tokens": rr.output_tokens,
            "scores": [
                {
                    "metric_name": s.metric_name,
                    "score": s.score,
                    "score_metadata": s.score_metadata,
                    "scorer_version": s.scorer_version,
                    "judge_model_version": s.judge_model_version,
                    "scored_at": s.scored_at.isoformat() if s.scored_at else None,
                }
                for s in scores
            ],
        })

    report = {
        "meridian_version": "1.0.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "run": {
            "id": run.id,
            "name": run.name,
            "status": run.status,
            "config": run.config_json,
            "judge_provider": run.judge_provider,
            "judge_model_id": run.judge_model_id,
            "judge_model_version": run.judge_model_version,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "total_cells": run.total_cells,
            "succeeded_cells": run.succeeded_cells,
            "failed_cells": run.failed_cells,
        },
        "results": results_payload,
    }

    output = json.dumps(report, indent=2, default=str)
    filename = f"meridian_run_{run_id[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/runs/{run_id}/reports")
async def list_reports(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.run_id == run_id)
    )
    reports = result.scalars().all()
    return [
        {"id": r.id, "format": r.format, "file_path": r.file_path, "created_at": r.created_at}
        for r in reports
    ]
