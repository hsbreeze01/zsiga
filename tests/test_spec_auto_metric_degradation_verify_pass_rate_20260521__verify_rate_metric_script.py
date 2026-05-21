"""Tests for spec: verify-rate-metric-script

Tests for the compute_verify_rate_report function.
"""
import json

from zsiga.metrics.types import ChangeRecord, PhaseRecord, Phase, Outcome


def _make_change(name, project, outcome, verify_outcome=None, failure_category=None):
    """Helper to build a change dict for testing."""
    phases = []
    if verify_outcome is not None:
        p = {
            "phase": "verify",
            "outcome": verify_outcome,
            "seconds_used": 10.0,
        }
        if failure_category:
            p["failure_category"] = failure_category
        phases.append(p)
    return {
        "change_name": name,
        "project": project,
        "outcome": outcome,
        "started_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T01:00:00",
        "phases": phases,
    }


class TestComputeVerifyRateReport:
    """Test compute_verify_rate_report function."""

    def test_overall_verify_pass_rate(self):
        """Scenario: Report contains overall verify pass rate.

        3 changes with 2 verify pass → 66.7%.
        """
        from zsiga.metrics.verify_rate import compute_verify_rate_report

        changes = [
            _make_change("c1", "zsiga", "success", "success"),
            _make_change("c2", "zsiga", "success", "success"),
            _make_change("c3", "zsiga", "reverted", "fail", "lint"),
        ]
        report = compute_verify_rate_report(changes)
        assert abs(report["verify_pass_rate_pct"] - 66.7) < 0.2

    def test_per_project_breakdown(self):
        """Scenario: Report contains per-project breakdown."""
        from zsiga.metrics.verify_rate import compute_verify_rate_report

        changes = [
            _make_change("c1", "zsiga", "success", "success"),
            _make_change("c2", "zsiga", "reverted", "fail", "unknown"),
            _make_change("c3", "compass", "success", "success"),
            _make_change("c4", "compass", "reverted", "fail", "test"),
        ]
        report = compute_verify_rate_report(changes)
        assert "zsiga" in report["by_project"]
        assert "compass" in report["by_project"]

    def test_failure_breakdown_by_category(self):
        """Scenario: Report contains failure breakdown by category."""
        from zsiga.metrics.verify_rate import compute_verify_rate_report

        changes = [
            _make_change("c1", "zsiga", "reverted", "fail", "unknown"),
            _make_change("c2", "zsiga", "reverted", "fail", "unknown"),
            _make_change("c3", "zsiga", "reverted", "fail", "llm_judge"),
            _make_change("c4", "zsiga", "reverted", "fail", "lint"),
            _make_change("c5", "zsiga", "success", "success"),
        ]
        report = compute_verify_rate_report(changes)
        breakdown = report["failure_breakdown"]
        assert breakdown.get("unknown") == 2
        assert breakdown.get("llm_judge") == 1
        assert breakdown.get("lint") == 1

    def test_empty_changes_graceful(self):
        """Scenario: Report handles empty change list gracefully."""
        from zsiga.metrics.verify_rate import compute_verify_rate_report

        report = compute_verify_rate_report([])
        assert report["verify_pass_rate_pct"] == 0.0
        assert report["by_project"] == {}
        assert report["failure_breakdown"] == {}
        assert report["rolling_window"] == []
