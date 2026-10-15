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
    result = await db.execute(q)
    models = list(result.scalars().all())

    # Priority rank: Cloudflare -> Gemini -> Groq -> OpenRouter (lowest)
    prov_res = await db.execute(select(Provider))
    providers = {p.id: p.name.lower() for p in prov_res.scalars().all()}

    def provider_priority(model: Model) -> int:
        p_name = providers.get(model.provider_id, "")
        if "cloudflare" in p_name:
            return 1
        elif "gemini" in p_name or "google" in p_name:
            return 2
        elif "groq" in p_name:
            return 3
        elif "openrouter" in p_name:
            return 4
        return 5

    models.sort(key=lambda m: (provider_priority(m), m.display_name))
    return models


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


class ProviderKeyPayload(BaseModel):
    provider_name: str
    api_key: str
    extra: Optional[dict[str, str]] = None


@router.post("/providers/key")
async def update_provider_key(data: ProviderKeyPayload):
    """
    Save provider credentials securely to runtime environment and .env file.
    Updates the adapter registry immediately so changes take effect without server restart.
    Implements SRS FR-1.3 and PRD credential management.
    """
    import os
    import dotenv
    from app.adapters.registry import reset_adapters, list_configured_providers

    prov = data.provider_name.lower().strip()
    env_updates: dict[str, str] = {}

    if "cloudflare" in prov:
        env_updates["CLOUDFLARE_API_TOKEN"] = data.api_key.strip()
        if data.extra and data.extra.get("account_id"):
            env_updates["CLOUDFLARE_ACCOUNT_ID"] = data.extra["account_id"].strip()
    elif "gemini" in prov or "google" in prov:
        env_updates["GEMINI_API_KEY"] = data.api_key.strip()
    elif "groq" in prov:
        env_updates["GROQ_API_KEY"] = data.api_key.strip()
    elif "openrouter" in prov:
        env_updates["OPENROUTER_API_KEY"] = data.api_key.strip()
    else:
        key_var = f"{prov.upper()}_API_KEY"
        env_updates[key_var] = data.api_key.strip()

    # Update in-memory os.environ
    for k, v in env_updates.items():
        os.environ[k] = v

    # Persist to .env file
    env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend/.env"))
    if not os.path.exists(env_file):
        env_file = os.path.abspath(".env")

    try:
        for k, v in env_updates.items():
            dotenv.set_key(env_file, k, v)
    except Exception:
        pass

    # Clear cached singletons so new credentials apply
    reset_adapters()

    return {
        "status": "success",
        "provider": prov,
        "message": f"Successfully updated credentials for {data.provider_name}",
        "configured_providers": list_configured_providers(),
    }

