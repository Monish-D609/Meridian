"""
Meridian API — Datasets & Tasks endpoints.
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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


# ---------------------------------------------------------------------------
# Custom Dataset Upload & Validation (SRS FR-2.2 & FR-2.3)
# ---------------------------------------------------------------------------
class CustomTaskItem(BaseModel):
    prompt: str
    reference_answer: Optional[str] = None
    context: Optional[str] = None
    system_prompt: Optional[str] = None


class CustomDatasetPayload(BaseModel):
    name: str
    category_id: str
    description: Optional[str] = None
    task_type: str = "open"
    tasks: list[CustomTaskItem]


@router.post("/datasets/upload")
async def upload_custom_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    category_id: str = Form(...),
    description: Optional[str] = Form(None),
    task_type: Optional[str] = Form("open"),
    db: AsyncSession = Depends(get_db),
):
    """
    Custom dataset upload supporting CSV and JSON format.
    Validates schema: prompt (required non-empty string), reference_answer (optional),
    context (optional), system_prompt (optional). Datasets with malformed rows are
    rejected with clear explanatory errors.
    Implements SRS FR-2.2 and FR-2.3.
    """
    # 1. Resolve Category
    cat = await db.get(CapabilityCategory, category_id)
    if not cat:
        cat_res = await db.execute(
            select(CapabilityCategory).where(CapabilityCategory.slug == category_id.lower().strip())
        )
        cat = cat_res.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=400, detail=f"Capability category '{category_id}' not found.")

    # 2. Read and decode content
    content_bytes = await file.read()
    try:
        text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = content_bytes.decode("latin-1", errors="replace")

    filename = (file.filename or "").lower()
    is_json = filename.endswith(".json") or text.lstrip().startswith(("{", "["))

    raw_tasks = []
    if is_json:
        try:
            parsed = json.loads(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file format: {str(e)}")

        if isinstance(parsed, dict):
            raw_tasks = parsed.get("tasks", parsed.get("items", []))
            if not isinstance(raw_tasks, list):
                raise HTTPException(
                    status_code=400,
                    detail="JSON file must contain a 'tasks' list or be a root array of task objects.",
                )
        elif isinstance(parsed, list):
            raw_tasks = parsed
        else:
            raise HTTPException(
                status_code=400,
                detail="JSON root must be an array of task objects or an object with a 'tasks' array.",
            )
    else:
        try:
            reader = csv.DictReader(io.StringIO(text))
            raw_tasks = list(reader)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV file format: {str(e)}")

    if not raw_tasks:
        raise HTTPException(status_code=400, detail="Uploaded dataset must contain at least 1 task row.")

    # 3. Validate rows (FR-2.3)
    valid_tasks = []
    for idx, item in enumerate(raw_tasks):
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail=f"Row {idx + 1} is not a valid key-value object.")

        # Locate prompt
        prompt = None
        for k, v in item.items():
            if k and k.lower().strip() == "prompt":
                prompt = str(v).strip() if v is not None else None
                break

        if not prompt:
            raise HTTPException(
                status_code=400,
                detail=f"Row {idx + 1} is malformed: missing or empty required field 'prompt'.",
            )

        ref_ans = None
        ctx = None
        sys_prompt = None
        for k, v in item.items():
            k_clean = k.lower().strip() if k else ""
            if k_clean in ("reference_answer", "reference", "answer", "ground_truth"):
                ref_ans = str(v).strip() if v else None
            elif k_clean in ("context", "passage", "document", "retrieved_context"):
                ctx = str(v).strip() if v else None
            elif k_clean in ("system_prompt", "system", "instruction"):
                sys_prompt = str(v).strip() if v else None

        valid_tasks.append({
            "prompt": prompt,
            "reference_answer": ref_ans,
            "context": ctx,
            "system_prompt": sys_prompt,
        })

    # 4. Insert Dataset & Tasks
    ds_id = str(uuid.uuid4())
    ds = Dataset(
        id=ds_id,
        name=name.strip(),
        category_id=cat.id,
        description=description.strip() if description else f"Custom uploaded dataset ({len(valid_tasks)} tasks)",
        task_type=task_type or "open",
        version_tag="custom-upload",
    )
    db.add(ds)
    await db.flush()

    for t_data in valid_tasks:
        t = Task(
            id=str(uuid.uuid4()),
            dataset_id=ds_id,
            **t_data,
        )
        db.add(t)

    await db.flush()
    return {
        "id": ds.id,
        "name": ds.name,
        "category_id": ds.category_id,
        "category_name": cat.name,
        "task_count": len(valid_tasks),
        "message": f"Successfully uploaded and validated {len(valid_tasks)} benchmark tasks.",
    }


@router.post("/datasets/custom")
async def create_custom_dataset_json(
    payload: CustomDatasetPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Create custom dataset via direct JSON API payload.
    Fulfills SRS FR-2.2 and FR-2.3.
    """
    cat = await db.get(CapabilityCategory, payload.category_id)
    if not cat:
        cat_res = await db.execute(
            select(CapabilityCategory).where(CapabilityCategory.slug == payload.category_id.lower().strip())
        )
        cat = cat_res.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=400, detail=f"Capability category '{payload.category_id}' not found.")

    if not payload.tasks:
        raise HTTPException(status_code=400, detail="Custom dataset must include at least 1 task.")

    for idx, t in enumerate(payload.tasks):
        if not t.prompt or not t.prompt.strip():
            raise HTTPException(status_code=400, detail=f"Task {idx + 1} is missing a required prompt.")

    ds_id = str(uuid.uuid4())
    ds = Dataset(
        id=ds_id,
        name=payload.name.strip(),
        category_id=cat.id,
        description=payload.description or f"Custom dataset ({len(payload.tasks)} tasks)",
        task_type=payload.task_type or "open",
        version_tag="custom-json",
    )
    db.add(ds)
    await db.flush()

    for t in payload.tasks:
        task_rec = Task(
            id=str(uuid.uuid4()),
            dataset_id=ds_id,
            prompt=t.prompt.strip(),
            reference_answer=t.reference_answer.strip() if t.reference_answer else None,
            context=t.context.strip() if t.context else None,
            system_prompt=t.system_prompt.strip() if t.system_prompt else None,
        )
        db.add(task_rec)

    await db.flush()
    return {
        "id": ds.id,
        "name": ds.name,
        "category_id": ds.category_id,
        "category_name": cat.name,
        "task_count": len(payload.tasks),
        "message": f"Successfully created custom dataset '{ds.name}' with {len(payload.tasks)} tasks.",
    }

