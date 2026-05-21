"""
Per-role LLM provider router.

Reads env vars to decide which LLM backend each role/phase should use.
Supports two providers today:
- ``zhipuai`` (default): the existing ``zai.ZaiClient`` against the
  glm-5.1 coding API at https://open.bigmodel.cn/api/coding/paas/v4
- ``openai``: any OpenAI-compatible endpoint (DeepSeek, vLLM,
  Together, Groq, …).  Used here primarily for DeepSeek.

Env-var priority (high to low) for any *role*:

1. ``ZSIGA_<ROLE>_PROVIDER`` / ``ZSIGA_<ROLE>_API_KEY``
   / ``ZSIGA_<ROLE>_MODEL`` / ``ZSIGA_<ROLE>_BASE_URL``
   — fully explicit per-role override.
2. ``DEEPSEEK_API_KEY`` set + role ∈ ``ZSIGA_DEEPSEEK_ROLES``
   (default: ``review``)
   — convenience switch: drop a single env var to redirect a chosen
   subset of roles to DeepSeek.
3. fall through to the *default_profile* the caller already has from
   ``zsiga.yaml`` (i.e. zhipuai/glm-5.1).

This module is a pure helper — no SDK imports here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMProfile:
    """Resolved LLM call profile for a single role/phase."""

    provider: str       # "zhipuai" or "openai"
    api_key: str
    model: str
    base_url: str | None


# Default DeepSeek endpoint and model when only ``DEEPSEEK_API_KEY`` is set.
DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"
DEEPSEEK_DEFAULT_ROLES = "review"


def get_llm_profile(role: str, default: LLMProfile) -> LLMProfile:
    """Return the resolved LLM profile to use for *role*.

    *role* is a free-form short string identifying the call site.
    Conventional values: ``main``, ``review``, ``implement``,
    ``verify``, ``clarify``, ``enrich``, ``fix``, ``eval-fix``,
    ``intent-router``.

    *default* carries whatever the caller already has from
    ``zsiga.yaml`` and is used unchanged when no override applies.
    """
    role_upper = role.upper().replace("-", "_")

    # 1. Explicit per-role env override
    explicit_provider = os.getenv(f"ZSIGA_{role_upper}_PROVIDER")
    explicit_api_key = os.getenv(f"ZSIGA_{role_upper}_API_KEY")
    explicit_model = os.getenv(f"ZSIGA_{role_upper}_MODEL")
    explicit_base = os.getenv(f"ZSIGA_{role_upper}_BASE_URL")
    if explicit_provider or explicit_api_key:
        return LLMProfile(
            provider=explicit_provider or default.provider,
            api_key=explicit_api_key or default.api_key,
            model=explicit_model or default.model,
            base_url=explicit_base or default.base_url,
        )

    # 2. DeepSeek convenience switch
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        roles_csv = os.getenv("ZSIGA_DEEPSEEK_ROLES", DEEPSEEK_DEFAULT_ROLES)
        allowed = {r.strip().lower() for r in roles_csv.split(",") if r.strip()}
        if role.lower() in allowed:
            return LLMProfile(
                provider="openai",
                api_key=deepseek_key,
                model=os.getenv("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL),
                base_url=os.getenv(
                    "DEEPSEEK_BASE_URL", DEEPSEEK_DEFAULT_BASE_URL,
                ),
            )

    return default
