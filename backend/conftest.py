"""
Meridian — pytest conftest.py

Sets up the test environment:
  - Ensures PYTHONPATH includes backend/
  - Provides common fixtures
"""
import os
import sys

# Add backend root to path so `app.*` imports work
sys.path.insert(0, os.path.dirname(__file__))

import pytest


@pytest.fixture(autouse=True)
def clear_env_vars(monkeypatch):
    """
    Remove sensitive env vars before each test that doesn't set them.
    Individual tests that need keys use monkeypatch.setenv().
    """
    for var in ["GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"]:
        monkeypatch.delenv(var, raising=False)
