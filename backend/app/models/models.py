"""
Meridian ORM Models — all 11 entities from SRS §5 / SAD §3.8.

Entity relationships:
  Provider → Model (one-to-many)
  Dataset  → Task  (one-to-many)
  Dataset  → CapabilityCategory (many-to-one)
  BenchmarkRun → RunResult (one-to-many)
  RunResult → EvaluationScore (one-to-many)
  BaselineModel → BaselineScore (one-to-many)
  BaselineScore → CapabilityCategory (many-to-one)
  BenchmarkRun → Report (one-to-many)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
class Provider(Base):
    """
    An LLM provider (e.g., Groq, Gemini, OpenRouter).
    Auth credentials are stored encrypted via the security module — never raw.
    """
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # base_url is the provider's API endpoint root
    base_url: Mapped[Optional[str]] = mapped_column(String(500))
    # auth_env_var: name of the env-var holding the API key (never the key itself)
    auth_env_var: Mapped[Optional[str]] = mapped_column(String(100))
    # encrypted_api_key: Fernet-encrypted key stored at rest (NFR-3.4)
    encrypted_api_key: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    models: Mapped[list["Model"]] = relationship("Model", back_populates="provider")


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
class Model(Base):
    """
    A specific LLM registered in the platform.
    model_id_external is the identifier used in provider API calls (e.g., "llama-3.1-8b-instant").
    """
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    provider_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("providers.id"), nullable=False
    )
    model_id_external: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Per-provider rate limit hints (requests/min, tokens/min)
    rate_limit_rpm: Mapped[Optional[int]] = mapped_column(Integer)
    rate_limit_tpm: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    provider: Mapped["Provider"] = relationship("Provider", back_populates="models")
    run_results: Mapped[list["RunResult"]] = relationship(
        "RunResult", back_populates="model"
    )

    __table_args__ = (
        UniqueConstraint("provider_id", "model_id_external", name="uq_model_provider_external"),
    )


# ---------------------------------------------------------------------------
# CapabilityCategory
# ---------------------------------------------------------------------------
class CapabilityCategory(Base):
    """
    One of the 7 capability dimensions used in the Industry Comparison Engine:
    coding, mathematics, reasoning, creative_writing, summarization,
    factual_qa, long_context.
    """
    __tablename__ = "capability_categories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    datasets: Mapped[list["Dataset"]] = relationship(
        "Dataset", back_populates="capability_category"
    )
    baseline_scores: Mapped[list["BaselineScore"]] = relationship(
        "BaselineScore", back_populates="capability_category"
    )


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class Dataset(Base):
    """
    A named collection of Tasks belonging to a capability category.
    task_type: 'closed' (exact-match/F1) or 'open' (LLM-judge).
    """
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("capability_categories.id"), nullable=False
    )
    task_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # 'closed' | 'open'
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    license_info: Mapped[Optional[str]] = mapped_column(String(200))
    version_tag: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    capability_category: Mapped["CapabilityCategory"] = relationship(
        "CapabilityCategory", back_populates="datasets"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="dataset")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------
class Task(Base):
    """
    A single evaluation prompt within a Dataset.
    reference_answer: the gold standard for closed tasks.
    context: optional document/passage (e.g., for factual QA / long-context).
    extra_metadata: JSON blob for any task-specific fields.
    """
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text)   # grounding source
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="tasks")
    run_results: Mapped[list["RunResult"]] = relationship(
        "RunResult", back_populates="task"
    )


# ---------------------------------------------------------------------------
# BenchmarkRun
# ---------------------------------------------------------------------------
class BenchmarkRun(Base):
    """
    One complete benchmark execution: N models × M tasks.
    config_json: full serialized run configuration (reproducibility, SRS FR-3.5).
    judge_model_id / judge_model_version: the LLM-as-a-Judge used in this run.
    status: pending | running | completed | failed.
    """
    __tablename__ = "benchmark_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON)   # full config snapshot
    # Judge model identity stored for reproducibility (NFR-3.2 / SRS FR-3.5)
    judge_provider: Mapped[Optional[str]] = mapped_column(String(100))
    judge_model_id: Mapped[Optional[str]] = mapped_column(String(200))
    judge_model_version: Mapped[Optional[str]] = mapped_column(String(200))
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    # Counts for quick summary
    total_cells: Mapped[Optional[int]] = mapped_column(Integer)
    succeeded_cells: Mapped[Optional[int]] = mapped_column(Integer)
    failed_cells: Mapped[Optional[int]] = mapped_column(Integer)

    run_results: Mapped[list["RunResult"]] = relationship(
        "RunResult", back_populates="benchmark_run"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="benchmark_run"
    )


# ---------------------------------------------------------------------------
# RunResult
# ---------------------------------------------------------------------------
class RunResult(Base):
    """
    One cell in the task×model matrix: the raw response from one model on one task.
    status: pending | running | succeeded | failed | quota_exceeded | skipped.
    Incremental persistence: never discard partial results (NFR-3.3).
    """
    __tablename__ = "run_results"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("benchmark_runs.id"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("models.id"), nullable=False
    )
    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # Raw response
    response_text: Mapped[Optional[str]] = mapped_column(Text)
    # Token and latency (Efficiency module)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON)   # full provider response
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    scored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    benchmark_run: Mapped["BenchmarkRun"] = relationship(
        "BenchmarkRun", back_populates="run_results"
    )
    model: Mapped["Model"] = relationship("Model", back_populates="run_results")
    task: Mapped["Task"] = relationship("Task", back_populates="run_results")
    evaluation_scores: Mapped[list["EvaluationScore"]] = relationship(
        "EvaluationScore", back_populates="run_result"
    )

    __table_args__ = (
        UniqueConstraint("run_id", "model_id", "task_id", name="uq_run_model_task"),
    )


# ---------------------------------------------------------------------------
# EvaluationScore
# ---------------------------------------------------------------------------
class EvaluationScore(Base):
    """
    One metric's score for one RunResult.
    metric_name: e.g., 'exact_match', 'f1', 'semantic_similarity',
                       'llm_judge_quality', 'hallucination_rate',
                       'groundedness', 'consistency', 'latency_ms',
                       'cost_usd', 'capability_tier'
    scorer_version: identifies the scorer algorithm + version used (reproducibility).
    judge_model_version: if LLM-judge was used, which model/version (NFR-3.2).
    """
    __tablename__ = "evaluation_scores"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_result_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("run_results.id"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float)
    score_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # extra detail (e.g., claim list)
    scorer_version: Mapped[str] = mapped_column(String(100), nullable=False)
    judge_model_version: Mapped[Optional[str]] = mapped_column(String(200))  # if LLM-judge
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    run_result: Mapped["RunResult"] = relationship(
        "RunResult", back_populates="evaluation_scores"
    )


# ---------------------------------------------------------------------------
# BaselineModel
# ---------------------------------------------------------------------------
class BaselineModel(Base):
    """
    A reference/industry-standard model whose scores form the baseline set.
    version_tag + captured_date: mandatory for reproducibility (NFR-3.2).
    is_placeholder: True for illustrative/seed data that is not real measurements.
    """
    __tablename__ = "baseline_models"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    # ISO date string: when these scores were captured / published
    captured_date: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False)

    baseline_scores: Mapped[list["BaselineScore"]] = relationship(
        "BaselineScore", back_populates="baseline_model"
    )


# ---------------------------------------------------------------------------
# BaselineScore
# ---------------------------------------------------------------------------
class BaselineScore(Base):
    """
    A baseline model's performance on one capability category.
    raw_score: normalized 0–1 score for this category.
    distribution_mean / distribution_std: used by the Industry Comparison Engine
      for z-score normalization of candidate model scores.
    """
    __tablename__ = "baseline_scores"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    baseline_model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("baseline_models.id"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("capability_categories.id"), nullable=False
    )
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0–1.0
    # Pre-computed distribution stats across all baseline models for this category
    distribution_mean: Mapped[Optional[float]] = mapped_column(Float)
    distribution_std: Mapped[Optional[float]] = mapped_column(Float)

    baseline_model: Mapped["BaselineModel"] = relationship(
        "BaselineModel", back_populates="baseline_scores"
    )
    capability_category: Mapped["CapabilityCategory"] = relationship(
        "CapabilityCategory", back_populates="baseline_scores"
    )

    __table_args__ = (
        UniqueConstraint("baseline_model_id", "category_id", name="uq_baseline_model_category"),
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
class Report(Base):
    """
    An exported report generated from a BenchmarkRun.
    format: 'pdf' | 'csv' | 'json'.
    file_path: relative path within the exports directory.
    """
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("benchmark_runs.id"), nullable=False
    )
    format: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | csv | json
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    benchmark_run: Mapped["BenchmarkRun"] = relationship(
        "BenchmarkRun", back_populates="reports"
    )
