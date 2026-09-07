"""
Meridian API — Industry Baselines endpoints.

Exposes the Baseline Registry for reading and managing.
Baselines are versioned + date-stamped per NFR-3.2.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import BaselineModel, BaselineScore, CapabilityCategory

router = APIRouter()


class BaselineModelOut(BaseModel):
    id: str
    display_name: str
    version_tag: str
    captured_date: str
    notes: Optional[str]
    source_url: Optional[str]
    is_placeholder: bool
    model_config = {"from_attributes": True}


class BaselineScoreOut(BaseModel):
    id: str
    baseline_model_id: str
    category_id: str
    raw_score: float
    distribution_mean: Optional[float]
    distribution_std: Optional[float]
    model_config = {"from_attributes": True}


@router.get("/baselines", response_model=list[BaselineModelOut])
async def list_baselines(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BaselineModel).order_by(BaselineModel.captured_date.desc()))
    return result.scalars().all()


@router.get("/baselines/{baseline_id}", response_model=BaselineModelOut)
async def get_baseline(baseline_id: str, db: AsyncSession = Depends(get_db)):
    b = await db.get(BaselineModel, baseline_id)
    if not b:
        raise HTTPException(status_code=404, detail="Baseline model not found")
    return b


@router.get("/baselines/{baseline_id}/scores", response_model=list[BaselineScoreOut])
async def get_baseline_scores(baseline_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BaselineScore).where(BaselineScore.baseline_model_id == baseline_id)
    )
    return result.scalars().all()


@router.get("/baselines/distribution/{category_slug}")
async def get_baseline_distribution(
    category_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the score distribution for a capability category (for the Industry Comparison Engine)."""
    cat_result = await db.execute(
        select(CapabilityCategory).where(CapabilityCategory.slug == category_slug)
    )
    cat = cat_result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    scores_result = await db.execute(
        select(BaselineScore, BaselineModel)
        .join(BaselineModel, BaselineScore.baseline_model_id == BaselineModel.id)
        .where(BaselineScore.category_id == cat.id)
    )
    rows = scores_result.all()
    return {
        "category_slug": category_slug,
        "category_name": cat.name,
        "baselines": [
            {
                "baseline_model": r.BaselineModel.display_name,
                "version_tag": r.BaselineModel.version_tag,
                "captured_date": r.BaselineModel.captured_date,
                "is_placeholder": r.BaselineModel.is_placeholder,
                "raw_score": r.BaselineScore.raw_score,
            }
            for r in rows
        ],
        "distribution_mean": rows[0].BaselineScore.distribution_mean if rows else None,
        "distribution_std": rows[0].BaselineScore.distribution_std if rows else None,
    }
