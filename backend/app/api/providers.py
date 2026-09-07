"""
Meridian API — Providers & Models endpoints.

Provider API keys are NEVER returned in responses (NFR-3.4).
Keys are stored encrypted via the security module.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Model, Provider

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ProviderCreate(BaseModel):
    name: str
    base_url: Optional[str] = None
    auth_env_var: Optional[str] = None
    notes: Optional[str] = None


class ProviderOut(BaseModel):
    id: str
    name: str
    base_url: Optional[str]
    auth_env_var: Optional[str]
    is_active: bool
    notes: Optional[str]
    model_config = {"from_attributes": True}


class ModelCreate(BaseModel):
    provider_id: str
    model_id_external: str
    display_name: str
    description: Optional[str] = None
    rate_limit_rpm: Optional[int] = None
    rate_limit_tpm: Optional[int] = None


class ModelOut(BaseModel):
    id: str
    provider_id: str
    model_id_external: str
    display_name: str
    description: Optional[str]
    is_active: bool
    rate_limit_rpm: Optional[int]
    rate_limit_tpm: Optional[int]
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Provider endpoints
# ---------------------------------------------------------------------------
@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Provider).order_by(Provider.name))
    return result.scalars().all()


@router.get("/providers/{provider_id}", response_model=ProviderOut)
async def get_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Provider, provider_id)
    if not p:
        raise HTTPException(status_code=404, detail="Provider not found")
    return p


@router.post("/providers", response_model=ProviderOut, status_code=201)
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db)):
    import uuid
    p = Provider(id=str(uuid.uuid4()), **data.model_dump())
    db.add(p)
    await db.flush()
    return p


@router.patch("/providers/{provider_id}", response_model=ProviderOut)
async def update_provider(
    provider_id: str,
    data: ProviderCreate,
    db: AsyncSession = Depends(get_db),
):
    p = await db.get(Provider, provider_id)
    if not p:
        raise HTTPException(status_code=404, detail="Provider not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    return p


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Provider, provider_id)
    if not p:
        raise HTTPException(status_code=404, detail="Provider not found")
    p.is_active = False   # soft delete


# ---------------------------------------------------------------------------
# Model endpoints
# ---------------------------------------------------------------------------
@router.get("/models", response_model=list[ModelOut])
async def list_models(
    provider_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Model).where(Model.is_active == True)
    if provider_id:
        q = q.where(Model.provider_id == provider_id)
    result = await db.execute(q.order_by(Model.display_name))
    return result.scalars().all()


@router.get("/models/{model_id}", response_model=ModelOut)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    m = await db.get(Model, model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return m


@router.post("/models", response_model=ModelOut, status_code=201)
async def create_model(data: ModelCreate, db: AsyncSession = Depends(get_db)):
    import uuid
    # Validate provider exists
    p = await db.get(Provider, data.provider_id)
    if not p:
        raise HTTPException(status_code=400, detail="Provider not found")
    m = Model(id=str(uuid.uuid4()), **data.model_dump())
    db.add(m)
    await db.flush()
    return m


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    m = await db.get(Model, model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    m.is_active = False


@router.get("/providers/configured/list")
async def list_configured_providers():
    """Return providers that currently have API keys configured."""
    from app.adapters.registry import list_configured_providers
    return {"configured_providers": list_configured_providers()}
