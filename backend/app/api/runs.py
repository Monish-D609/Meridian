"""
Meridian API — Benchmark Runs endpoints.

Includes:
  POST /runs         — create and start a benchmark run
  GET  /runs         — list all runs
  GET  /runs/{id}    — get run details
  GET  /runs/{id}/progress — poll for run progress (SRS FR-3.x)
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, get_db
from app.manager.run_manager import create_run, get_run_progress
from app.models.models import BenchmarkRun

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RunCreate(BaseModel):
    name: str
    model_ids: list[str]
    dataset_ids: list[str]
    description: Optional[str] = ""
    max_tokens: int = 1024
    temperature: float = 0.0
    task_mix_mode: Optional[str] = "standard"


class RunOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    judge_provider: Optional[str]
    judge_model_id: Optional[str]
    judge_model_version: Optional[str]
    config_json: Optional[dict]
    total_cells: Optional[int]
    succeeded_cells: Optional[int]
    failed_cells: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/runs", response_model=list[RunOut])
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc())
    )
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/progress")
async def run_progress(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Poll-based progress endpoint for run status.
    Frontend polls this every 2–5 seconds during a run.
    (SRS FR-3.x — progress tracking)
    """
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    progress = await get_run_progress(run_id, db)
    progress["status"] = run.status
    progress["run_status"] = run.status
    return progress


@router.post("/runs", response_model=RunOut, status_code=202)
async def create_and_start_run(
    data: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a benchmark run and immediately kick off async execution.
    Returns immediately with status='pending'; poll /runs/{id}/progress for updates.
    """
    from app.manager.run_manager import execute_run

    try:
        run = await create_run(
            session=db,
            name=data.name,
            model_ids=data.model_ids,
            dataset_ids=data.dataset_ids,
            description=data.description or "",
            max_tokens=data.max_tokens,
            temperature=data.temperature,
            task_mix_mode=data.task_mix_mode or "standard",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Execute in background — do not await (runs asynchronously)
    background_tasks.add_task(execute_run, run.id, AsyncSessionLocal)

    return run


@router.post("/runs/{run_id}/stop")
async def stop_run_endpoint(run_id: str, db: AsyncSession = Depends(get_db)):
    """
    Stop an ongoing benchmark run immediately.
    Halts remaining pending cells, updates tallies, and produces results
    only for the tests conducted so far.
    """
    from app.manager.run_manager import stop_run

    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status in ("completed", "failed", "stopped"):
        return {"message": f"Run is already {run.status}", "status": run.status, "run_id": run_id}

    stopped = await stop_run(run_id, AsyncSessionLocal)
    return {
        "message": "Run stopped successfully. Results compiled for conducted tests.",
        "status": stopped.status,
        "run_id": run_id,
        "succeeded_cells": stopped.succeeded_cells,
        "failed_cells": stopped.failed_cells,
    }


@router.delete("/runs/{run_id}", status_code=204)
async def delete_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status == "running":
        raise HTTPException(status_code=409, detail="Cannot delete a running run")
    await db.delete(run)
