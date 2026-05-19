"""Intent Router capability test suite.

Validates classify() and route() from zsiga.agent.intent_router across all six
IntentType categories.  _classify_via_llm is mocked to return None so that the
keyword-path logic is deterministically exercised.
"""

import pytest
from unittest.mock import patch

from zsiga.agent.intent_router import (
    Intent,
    IntentType,
    classify,
    route,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _disable_llm(monkeypatch):
    """Ensure _classify_via_llm always returns None (keyword path only)."""
    import zsiga.agent.intent_router as ir

    monkeypatch.setattr(ir, "_classify_via_llm", lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# Test data: >= 20 messages, >= 3 per IntentType
# ---------------------------------------------------------------------------

_CLASSIFICATION_CASES = [
    # --- RESEARCH (>= 3) ---
    ("how does the event loop work in this project?", IntentType.RESEARCH),
    ("explain the caching strategy used", IntentType.RESEARCH),
    ("help me understand the auth flow", IntentType.RESEARCH),
    ("看看这个模块怎么运行的", IntentType.RESEARCH),
    ("分析一下性能瓶颈", IntentType.RESEARCH),
    # --- IMPLEMENTATION (>= 3) ---
    ("implement user authentication module", IntentType.IMPLEMENTATION),
    ("add a new REST API endpoint for payments", IntentType.IMPLEMENTATION),
    ("create the database migration script", IntentType.IMPLEMENTATION),
    ("build a caching layer for the service", IntentType.IMPLEMENTATION),
    ("开发一个新的功能模块", IntentType.IMPLEMENTATION),
    # --- INVESTIGATION (>= 3) ---
    ("debug the memory leak in worker process", IntentType.INVESTIGATION),
    ("investigate why the service is crashing", IntentType.INVESTIGATION),
    ("diagnose the timeout errors in production", IntentType.INVESTIGATION),
    ("排查线上接口报错问题", IntentType.INVESTIGATION),
    # --- EVALUATION (>= 3) ---
    ("review the PR for security issues", IntentType.EVALUATION),
    ("compare performance of approach A vs B", IntentType.EVALUATION),
    ("assess code quality of the payment module", IntentType.EVALUATION),
    ("评估这个方案的风险", IntentType.EVALUATION),
    # --- FIX (>= 3) ---
    ("fix the failing test in test_auth.py", IntentType.FIX),
    ("patch the security vulnerability in login", IntentType.FIX),
    ("修复构建失败的问题", IntentType.FIX),
    # --- OPEN_ENDED (>= 3) ---
    ("", IntentType.OPEN_ENDED),
    ("   ", IntentType.OPEN_ENDED),
    ("\t\n", IntentType.OPEN_ENDED),
]


# ---------------------------------------------------------------------------
# Scenario: Six-category classification coverage
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("message,expected_type", _CLASSIFICATION_CASES)
def test_classify_matches_expected_category(message, expected_type):
    result = classify(message)
    assert result.intent_type == expected_type, (
        f"Message {message!r}: expected {expected_type.value}, "
        f"got {result.intent_type.value}"
    )


def test_at_least_3_per_category():
    """Ensure every IntentType has at least 3 test cases."""
    counts: dict[IntentType, int] = {}
    for _, expected_type in _CLASSIFICATION_CASES:
        counts[expected_type] = counts.get(expected_type, 0) + 1

    for itype in IntentType:
        assert counts.get(itype, 0) >= 3, (
            f"IntentType {itype.value} has only {counts.get(itype, 0)} cases, need >= 3"
        )

    total = len(_CLASSIFICATION_CASES)
    assert total >= 20, f"Need >= 20 cases, got {total}"


# ---------------------------------------------------------------------------
# Scenario: Construction verb with search keyword disambiguation
# ---------------------------------------------------------------------------

def test_implement_search_feature_is_implementation():
    """'implement search feature for user profiles' → IMPLEMENTATION, not RESEARCH."""
    result = classify("implement search feature for user profiles")
    assert result.intent_type == IntentType.IMPLEMENTATION


def test_build_explorer_tool_is_implementation():
    """'build an explorer tool' → IMPLEMENTATION."""
    result = classify("build an explorer tool feature")
    assert result.intent_type == IntentType.IMPLEMENTATION


def test_add_search_endpoint_is_implementation():
    """'add search API endpoint' → IMPLEMENTATION."""
    result = classify("add search API endpoint for user lookup")
    assert result.intent_type == IntentType.IMPLEMENTATION


# ---------------------------------------------------------------------------
# Scenario: Investigation keyword coverage including "investigate"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message",
    [
        "investigate the root cause of memory leak",
        "diagnose connection timeout issues",
        "排查线上服务异常",
    ],
)
def test_investigation_keywords(message):
    result = classify(message)
    assert result.intent_type == IntentType.INVESTIGATION


# ---------------------------------------------------------------------------
# Scenario: Empty input returns OPEN_ENDED
# ---------------------------------------------------------------------------

def test_empty_string_returns_open_ended():
    result = classify("")
    assert result.intent_type == IntentType.OPEN_ENDED
    assert result.confidence >= 0.9


def test_whitespace_only_returns_open_ended():
    result = classify("   \t\n  ")
    assert result.intent_type == IntentType.OPEN_ENDED
    assert result.confidence >= 0.9


# ---------------------------------------------------------------------------
# Scenario: Route mapping correctness
# ---------------------------------------------------------------------------

_ROUTE_CASES = [
    (IntentType.RESEARCH, "dispatch_explore"),
    (IntentType.IMPLEMENTATION, "pipeline"),
    (IntentType.INVESTIGATION, "dispatch_diagnoser"),
    (IntentType.EVALUATION, "dispatch_review"),
    (IntentType.FIX, "pipeline_fix"),
    (IntentType.OPEN_ENDED, "ask_user"),
]


@pytest.mark.parametrize("intent_type,expected_route", _ROUTE_CASES)
def test_route_mapping(intent_type, expected_route):
    intent = Intent(
        verbalization="test",
        intent_type=intent_type,
        confidence=0.8,
        reasoning="test",
        suggested_action="test",
    )
    assert route(intent) == expected_route


# ---------------------------------------------------------------------------
# Scenario: Verbalization is non-empty for all inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message",
    [
        "implement user auth",
        "fix the broken test",
        "how does caching work",
        "review the code",
        "debug the crash",
        "hello world",
    ],
)
def test_verbalization_non_empty(message):
    result = classify(message)
    assert isinstance(result.verbalization, str)
    assert len(result.verbalization.strip()) > 0
