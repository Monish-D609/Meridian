"""
Meridian — Adapter Registry.

Config-driven registry: resolves a provider name → adapter instance.
New providers require only a new adapter module + one line here.
This fulfills SRS NFR-3.2 (adding a provider requires only a new adapter module).
"""
from __future__ import annotations

from typing import Optional

from app.adapters.base import BaseAdapter
from app.adapters.cloudflare_adapter import CloudflareAdapter
from app.adapters.gemini_adapter import GeminiAdapter
from app.adapters.groq_adapter import GroqAdapter
from app.adapters.nim_adapter import NIMAdapter
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.adapters.xai_adapter import XAIAdapter

# ---------------------------------------------------------------------------
# Registry: provider_name → adapter class
# ---------------------------------------------------------------------------
_ADAPTER_CLASSES: dict[str, type[BaseAdapter]] = {
    "groq": GroqAdapter,
    "gemini": GeminiAdapter,
    "google": GeminiAdapter,          # alias
    "openrouter": OpenRouterAdapter,
    "cloudflare": CloudflareAdapter,
    "nvidia_nim": NIMAdapter,
    "nim": NIMAdapter,               # alias
    "xai": XAIAdapter,
    "grok": XAIAdapter,              # alias
}

# Singletons (one instance per provider, created on first access)
_instances: dict[str, BaseAdapter] = {}


def reset_adapters() -> None:
    """Clear cached adapter singletons so new environment credentials take effect."""
    _instances.clear()


def get_adapter(provider_name: str) -> Optional[BaseAdapter]:
    """
    Return the adapter instance for a given provider name (case-insensitive).
    Returns None if the provider is unknown.
    """
    key = provider_name.lower().strip()
    if key not in _ADAPTER_CLASSES:
        return None
    if key not in _instances:
        _instances[key] = _ADAPTER_CLASSES[key]()
    return _instances[key]


def list_providers() -> list[str]:
    """Return all registered provider names (canonical, no aliases)."""
    seen = set()
    result = []
    for cls in _ADAPTER_CLASSES.values():
        name = cls.provider_name
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def list_configured_providers() -> list[str]:
    """Return only providers that are currently configured (have API keys)."""
    result = []
    for name in list_providers():
        adapter = get_adapter(name)
        if adapter and adapter.is_configured():
            result.append(name)
    return result
