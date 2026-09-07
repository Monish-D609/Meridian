"""
Meridian API — Datasets & Tasks endpoints.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import CapabilityCategory, Dataset, Task

router = APIRouter()


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    model_config = {"from_attributes": True}


class DatasetOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category_id: str
    task_type: str
    source_url: Optional[str]
    license_info: Optional[str]
    version_tag: Optional[str]
    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: str
    dataset_id: str
    prompt: str
    reference_answer: Optional[str]
    context: Optional[str]
    system_prompt: Optional[str]
    model_config = {"from_attributes": True}


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: str
    task_type: str = "open"
    source_url: Optional[str] = None
    license_info: Optional[str] = None
    version_tag: Optional[str] = None


class TaskCreate(BaseModel):
    dataset_id: str
    prompt: str
    reference_answer: Optional[str] = None
    context: Optional[str] = None
    system_prompt: Optional[str] = None


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CapabilityCategory).order_by(CapabilityCategory.name))
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets(
    category_slug: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Dataset)
    if category_slug:
        cat_result = await db.execute(
            select(CapabilityCategory).where(CapabilityCategory.slug == category_slug)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            q = q.where(Dataset.category_id == cat.id)
    result = await db.execute(q.order_by(Dataset.name))
    return result.scalars().all()


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    d = await db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return d


@router.post("/datasets", response_model=DatasetOut, status_code=201)
async def create_dataset(data: DatasetCreate, db: AsyncSession = Depends(get_db)):
    import uuid
    d = Dataset(id=str(uuid.uuid4()), **data.model_dump())
    db.add(d)
    await db.flush()
    return d


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
@router.get("/datasets/{dataset_id}/tasks", response_model=list[TaskOut])
async def list_tasks(dataset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.dataset_id == dataset_id)
    )
    return result.scalars().all()


@router.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    import uuid
    t = Task(id=str(uuid.uuid4()), **data.model_dump())
    db.add(t)
    await db.flush()
    return t


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    t = await db.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t
