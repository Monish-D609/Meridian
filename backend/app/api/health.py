"""Meridian API — Health Check"""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health", summary="Health check")
async def health():
    return {
        "status": "ok",
        "service": "meridian-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/", include_in_schema=False)
async def root():
    return {"message": "Meridian LLM Evaluation Platform — see /docs"}
