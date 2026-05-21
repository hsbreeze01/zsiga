"""Unit tests for zsiga.agent.llm_router."""
import os

import pytest

from zsiga.agent.llm_router import (
    DEEPSEEK_DEFAULT_BASE_URL,
    DEEPSEEK_DEFAULT_MODEL,
    LLMProfile,
    get_llm_profile,
)


@pytest.fixture
def default_profile() -> LLMProfile:
    return LLMProfile(
        provider="zhipuai",
        api_key="glm-key",
        model="glm-5.1",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
    )


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure none of the override env vars leak between tests."""
    for k in (
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_MODEL",
        "DEEPSEEK_BASE_URL",
        "ZSIGA_DEEPSEEK_ROLES",
    ):
        monkeypatch.delenv(k, raising=False)
    for role in ("REVIEW", "IMPLEMENT", "VERIFY", "MAIN"):
        for suf in ("PROVIDER", "API_KEY", "MODEL", "BASE_URL"):
            monkeypatch.delenv(f"ZSIGA_{role}_{suf}", raising=False)
    yield


def test_default_returned_unchanged_when_no_overrides(default_profile):
    out = get_llm_profile("review", default_profile)
    assert out is default_profile


def test_deepseek_key_routes_review_only_by_default(monkeypatch, default_profile):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    review = get_llm_profile("review", default_profile)
    impl = get_llm_profile("implement", default_profile)
    assert review.provider == "openai"
    assert review.api_key == "sk-ds"
    assert review.model == DEEPSEEK_DEFAULT_MODEL
    assert review.base_url == DEEPSEEK_DEFAULT_BASE_URL
    # implement keeps the default
    assert impl is default_profile


def test_deepseek_role_allowlist_widens_routing(monkeypatch, default_profile):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    monkeypatch.setenv("ZSIGA_DEEPSEEK_ROLES", "review, implement")
    impl = get_llm_profile("implement", default_profile)
    assert impl.provider == "openai"
    assert impl.model == DEEPSEEK_DEFAULT_MODEL
    # other role still default
    other = get_llm_profile("verify", default_profile)
    assert other is default_profile


def test_explicit_per_role_override_beats_deepseek_shortcut(monkeypatch, default_profile):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    monkeypatch.setenv("ZSIGA_REVIEW_PROVIDER", "openai")
    monkeypatch.setenv("ZSIGA_REVIEW_API_KEY", "sk-explicit")
    monkeypatch.setenv("ZSIGA_REVIEW_MODEL", "deepseek-coder")
    monkeypatch.setenv("ZSIGA_REVIEW_BASE_URL", "https://other-host/v1")
    out = get_llm_profile("review", default_profile)
    assert out.provider == "openai"
    assert out.api_key == "sk-explicit"
    assert out.model == "deepseek-coder"
    assert out.base_url == "https://other-host/v1"


def test_explicit_partial_override_fills_with_default(monkeypatch, default_profile):
    monkeypatch.setenv("ZSIGA_REVIEW_PROVIDER", "openai")
    monkeypatch.setenv("ZSIGA_REVIEW_API_KEY", "sk-explicit")
    out = get_llm_profile("review", default_profile)
    assert out.provider == "openai"
    assert out.api_key == "sk-explicit"
    # model + base_url unchanged
    assert out.model == default_profile.model
    assert out.base_url == default_profile.base_url


def test_deepseek_model_and_base_url_overridable(monkeypatch, default_profile):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://example.com/v9")
    out = get_llm_profile("review", default_profile)
    assert out.model == "deepseek-reasoner"
    assert out.base_url == "https://example.com/v9"


def test_role_lookup_is_case_insensitive_and_handles_dashes(monkeypatch, default_profile):
    monkeypatch.setenv("ZSIGA_EVAL_FIX_PROVIDER", "openai")
    monkeypatch.setenv("ZSIGA_EVAL_FIX_API_KEY", "sk-eval")
    out = get_llm_profile("eval-fix", default_profile)
    assert out.provider == "openai"
    assert out.api_key == "sk-eval"


def test_unknown_role_returns_default(monkeypatch, default_profile):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    out = get_llm_profile("totally-new-role", default_profile)
    # default allowlist is just "review" — anything else falls through
    assert out is default_profile
