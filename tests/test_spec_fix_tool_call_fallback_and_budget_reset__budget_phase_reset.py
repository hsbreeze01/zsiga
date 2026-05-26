"""Tests for budget phase reset and BUDGET_EXCEEDED outcome spec.

Generated from: specs/budget-phase-reset.md
Change: fix-tool-call-fallback-and-budget-reset

Covers testable scenarios:
- BUDGET_EXCEEDED content returns Outcome.FAIL
- Normal content returns default Outcome.SUCCESS
- TIMEOUT content returns default Outcome.SUCCESS
- STALE_LIMIT content returns default Outcome.SUCCESS
- None content does not raise and returns default
- set_phase resets all budget counters
"""
from unittest.mock import patch

from zsiga.agent.loop import RunResult
from zsiga.metrics.types import Outcome


def _resolve(result: RunResult, default: Outcome) -> Outcome:
    """Import helper for the not-yet-implemented function."""
    from zsiga.pipeline.orchestrator import _resolve_budget_exceeded
    return _resolve_budget_exceeded(result, default)


class TestResolveBudgetExceeded:
    """Scenario group: _resolve_budget_exceeded helper."""

    def test_budget_exceeded_returns_fail(self):
        """BUDGET_EXCEEDED content returns Outcome.FAIL."""
        result = RunResult(
            content="BUDGET_EXCEEDED",
            llm_calls=3, tool_calls=0, elapsed_seconds=10.0,
        )
        assert _resolve(result, Outcome.SUCCESS) is Outcome.FAIL

    def test_normal_content_returns_success(self):
        """Normal content returns default Outcome.SUCCESS."""
        result = RunResult(
            content="Here are the enriched specs...",
            llm_calls=5, tool_calls=10, elapsed_seconds=30.0,
        )
        assert _resolve(result, Outcome.SUCCESS) is Outcome.SUCCESS

    def test_timeout_returns_success(self):
        """TIMEOUT content returns default Outcome.SUCCESS."""
        result = RunResult(
            content="TIMEOUT",
            llm_calls=8, tool_calls=5, elapsed_seconds=120.0,
        )
        assert _resolve(result, Outcome.SUCCESS) is Outcome.SUCCESS

    def test_stale_limit_returns_success(self):
        """STALE_LIMIT content returns default Outcome.SUCCESS."""
        result = RunResult(
            content="STALE_LIMIT",
            llm_calls=4, tool_calls=3, elapsed_seconds=60.0,
        )
        assert _resolve(result, Outcome.SUCCESS) is Outcome.SUCCESS

    def test_none_content_returns_success(self):
        """None content does not raise and returns default."""
        result = RunResult(
            content=None,
            llm_calls=0, tool_calls=0, elapsed_seconds=0.0,
        )
        assert _resolve(result, Outcome.SUCCESS) is Outcome.SUCCESS

    def test_default_fail_preserved_for_non_budget(self):
        """When default is FAIL and content is normal, FAIL is preserved."""
        result = RunResult(
            content="some output",
            llm_calls=1, tool_calls=0, elapsed_seconds=1.0,
        )
        assert _resolve(result, Outcome.FAIL) is Outcome.FAIL

    def test_budget_exceeded_always_fail(self):
        """When content is BUDGET_EXCEEDED, always returns FAIL."""
        result = RunResult(
            content="BUDGET_EXCEEDED",
            llm_calls=2, tool_calls=0, elapsed_seconds=5.0,
        )
        assert _resolve(result, Outcome.FAIL) is Outcome.FAIL


class TestSetPhaseResetsBudgetCounters:
    """Scenario: set_phase resets all budget counters."""

    def test_set_phase_resets_used_extended_stale(self):
        """After dirty budget state, set_phase resets all counters to zero."""
        with patch("zsiga.agent.loop._build_llm_client"):
            from zsiga.agent.loop import AgentLoop
            loop = AgentLoop(api_key="test-key")

        # Simulate dirty budget state from a previous phase
        loop.budget._used = 500000
        loop.budget._extended = True
        loop.budget._consecutive_stale = 3

        # Act
        loop.set_phase("verify")

        # Assert all counters are reset
        assert loop.budget._used == 0
        assert loop.budget._extended is False
        assert loop.budget._consecutive_stale == 0

    def test_set_phase_updates_phase_label(self):
        """set_phase also updates the internal phase label."""
        with patch("zsiga.agent.loop._build_llm_client"):
            from zsiga.agent.loop import AgentLoop
            loop = AgentLoop(api_key="test-key")

        assert loop._phase_label == ""
        loop.set_phase("enrich")
        assert loop._phase_label == "enrich"
        loop.set_phase("verify")
        assert loop._phase_label == "verify"
