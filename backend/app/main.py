"""
Meridian — FastAPI Application Entry Point.

Architecture (SAD §3.2):
  Frontend → REST API → Benchmark Manager → LLM Integration Layer
           → Evaluation Engine → Industry Comparison Engine → DB

Security (NFR-3.4):
  - API keys never returned to frontend
  - API keys stored encrypted at rest
  - All external LLM calls happen server-side only

CORS is configured for the React frontend origin (set via CORS_ORIGINS env var).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, engine

# API routers
from app.api import (
    baselines,
    datasets,
    health,
    providers,
    reports,
    results,
    runs,
)

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: create tables on startup (idempotent)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Meridian startup: ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Meridian startup complete.")
    yield
    logger.info("Meridian shutdown.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Meridian — LLM Evaluation & Benchmarking Platform",
    description=(
        "Evaluate LLMs across capability categories and position them "
        "against industry-standard baselines using the Industry Comparison Engine. "
        "Built as a zero-budget academic project (SRS v1.0)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS (allow React frontend, configurable)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router,     prefix="",           tags=["Health"])
app.include_router(providers.router,  prefix="/api/v1",    tags=["Providers & Models"])
app.include_router(datasets.router,   prefix="/api/v1",    tags=["Datasets & Tasks"])
app.include_router(runs.router,       prefix="/api/v1",    tags=["Benchmark Runs"])
app.include_router(results.router,    prefix="/api/v1",    tags=["Run Results"])
app.include_router(baselines.router,  prefix="/api/v1",    tags=["Industry Baselines"])
app.include_router(reports.router,    prefix="/api/v1",    tags=["Reports"])
