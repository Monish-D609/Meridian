"""
Meridian — Application configuration via Pydantic Settings.
Reads from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://meridian:meridian@localhost:5432/meridian"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://meridian:meridian@localhost:5432/meridian"

    # -------------------------------------------------------------------------
    # LLM Provider API Keys (Cloudflare, Groq, Gemini, OpenRouter)
    # -------------------------------------------------------------------------
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""

    # -------------------------------------------------------------------------
    # LLM-as-a-Judge — stored per BenchmarkRun for reproducibility (SRS FR-3.5)
    # -------------------------------------------------------------------------
    JUDGE_PROVIDER: str = "cloudflare"
    JUDGE_MODEL: str = "@cf/meta/llama-3.1-8b-instruct"
    JUDGE_MODEL_VERSION: str = "llama-3.1-8b-instruct-cf"

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    ENCRYPTION_KEY: str = ""   # Fernet key for API key encryption at rest
    SECRET_KEY: str = "change-me-in-production"

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    def get_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # -------------------------------------------------------------------------
    # Industry Comparison Engine — Tier thresholds (configurable per SRS FR-6.x)
    # Percentile-based: score >= threshold → that tier
    # -------------------------------------------------------------------------
    TIER_FRONTIER_THRESHOLD: float = 0.80   # >= 80th percentile → Frontier
    TIER_STRONG_THRESHOLD: float = 0.60     # >= 60th percentile → Strong
    TIER_MID_THRESHOLD: float = 0.40        # >= 40th percentile → Mid
    # Below 40th percentile → Weak


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
