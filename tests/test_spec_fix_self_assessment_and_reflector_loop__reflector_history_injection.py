"""Tests for spec: reflector-history-injection.

Verifies _load_recent_failures helper and that generate_proposal
injects past failure history into proposal.md content.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.intake.reflector import Reflector, Signal


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def reflector():
    return Reflector()


@pytest.fixture
def base(tmp_path):
    (tmp_path / "memory").mkdir()
    (tmp_path / "openspec" / "changes").mkdir(parents=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "metrics").mkdir()
    return tmp_path


def _make_change(name: str, outcome: str = "success", phases: list | None = None) -> dict:
    return {
        "change_name": name,
        "project": "zsiga",
        "outcome": outcome,
        "started_at": "",
        "finished_at": "",
        "lessons_count": 0,
        "phases": phases or [],
    }


def _make_verify_fail_phases(detail: str = "unknown") -> list[dict]:
    return [
        {"phase": "IMPLEMENT", "outcome": "SUCCESS", "detail": ""},
        {"phase": "VERIFY", "outcome": "FAIL", "detail": detail},
    ]


# ── Scenario: load-recent-failures-returns-reverted ──────────

class TestLoadRecentFailuresReturnsReverted:
    """_load_recent_failures returns dicts with change_name and fail_reason."""

    def test_returns_matching_reverted_changes(self, reflector, base):
        changes = [
            _make_change("auto-metric_degradation-verify_pass_rate-001", "reverted",
                         _make_verify_fail_phases("lint error: E701")),
            _make_change("auto-metric_degradation-verify_pass_rate-002", "reverted",
                         _make_verify_fail_phases("test failed: assert False")),
            _make_change("auto-metric_degradation-verify_pass_rate-003", "success"),
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "verify_pass_rate", limit=3,
            )

        assert len(result) == 2
        for entry in result:
            assert "change_name" in entry
            assert "fail_reason" in entry
        assert result[0]["change_name"] == "auto-metric_degradation-verify_pass_rate-001"
        assert "lint error" in result[0]["fail_reason"]
        assert result[1]["change_name"] == "auto-metric_degradation-verify_pass_rate-002"
        assert "test failed" in result[1]["fail_reason"]

    def test_extracts_verify_detail(self, reflector, base):
        """fail_reason is extracted from VERIFY phase detail."""
        changes = [
            _make_change(
                "auto-recurring_failure-pipeline-fail-001",
                "reverted",
                _make_verify_fail_phases("import not found in module"),
            ),
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "pipeline-fail", limit=3,
            )

        assert len(result) == 1
        assert result[0]["fail_reason"] == "import not found in module"

    def test_unknown_when_no_verify_detail(self, reflector, base):
        """When no VERIFY phase detail, fail_reason defaults to 'unknown'."""
        changes = [
            _make_change(
                "auto-recurring_failure-pipeline-fail-001",
                "reverted",
                [{"phase": "IMPLEMENT", "outcome": "FAIL", "detail": "impl failed"}],
            ),
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "pipeline-fail", limit=3,
            )

        assert len(result) == 1
        assert result[0]["fail_reason"] == "unknown"


# ── Scenario: load-recent-failures-caps-at-limit ─────────────

class TestLoadRecentFailuresCapsAtLimit:
    """_load_recent_failures respects the limit parameter."""

    def test_caps_at_limit_3(self, reflector, base):
        changes = [
            _make_change(f"auto-metric_degradation-verify_pass_rate-{i:03d}", "reverted",
                         _make_verify_fail_phases(f"error {i}"))
            for i in range(5)
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "verify_pass_rate", limit=3,
            )
        assert len(result) == 3

    def test_returns_all_when_under_limit(self, reflector, base):
        changes = [
            _make_change(f"auto-metric_degradation-verify_pass_rate-{i:03d}", "reverted",
                         _make_verify_fail_phases(f"error {i}"))
            for i in range(2)
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "verify_pass_rate", limit=5,
            )
        assert len(result) == 2


# ── Scenario: load-recent-failures-returns-empty-when-none ───

class TestLoadRecentFailuresReturnsEmpty:
    """Returns empty list when no matching reverted changes exist."""

    def test_no_matching_changes(self, reflector, base):
        changes = [
            _make_change("auto-metric_degradation-success_rate-001", "reverted"),
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "verify_pass_rate", limit=3,
            )
        assert result == []

    def test_no_changes_at_all(self, reflector, base):
        with patch.object(reflector, "_load_recent_changes", return_value=[]):
            result = reflector._load_recent_failures(
                base, "verify_pass_rate", limit=3,
            )
        assert result == []

    def test_all_successful(self, reflector, base):
        changes = [
            _make_change("auto-metric_degradation-verify_pass_rate-001", "success"),
        ]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._load_recent_failures(
                base, "verify_pass_rate", limit=3,
            )
        assert result == []


# ── Scenario: proposal-md-contains-past-failures-section ─────

class TestProposalMdContainsPastFailures:
    """generate_proposal injects ## Past Failures when failures exist."""

    def test_past_failures_section_present(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Low verify rate",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        failures = [
            {"change_name": "auto-metric-verify_pass_rate-001", "fail_reason": "lint error"},
            {"change_name": "auto-metric-verify_pass_rate-002", "fail_reason": "test failed"},
        ]
        with patch.object(reflector, "_load_recent_failures", return_value=failures):
            result_path = reflector.generate_proposal(signal, base)

        assert result_path is not None
        content = (Path(result_path) / "proposal.md").read_text(encoding="utf-8")
        assert "## Past Failures" in content
        assert "auto-metric-verify_pass_rate-001" in content
        assert "auto-metric-verify_pass_rate-002" in content

    def test_past_failures_positioned_after_motivation(self, reflector, base):
        """## Past Failures appears after ## Motivation and before ## Expected Behavior."""
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Low verify rate",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        failures = [
            {"change_name": "auto-metric-verify_pass_rate-001", "fail_reason": "lint error"},
        ]
        with patch.object(reflector, "_load_recent_failures", return_value=failures):
            result_path = reflector.generate_proposal(signal, base)

        content = (Path(result_path) / "proposal.md").read_text(encoding="utf-8")
        motivation_pos = content.find("## Motivation")
        failures_pos = content.find("## Past Failures")
        expected_pos = content.find("## Expected Behavior")
        assert motivation_pos > 0
        assert failures_pos > motivation_pos
        assert expected_pos > failures_pos


# ── Scenario: proposal-md-no-past-failures-when-clean ────────

class TestProposalMdNoPastFailuresWhenClean:
    """No ## Past Failures section when no failure history exists."""

    def test_no_past_failures_section(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Low verify rate",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        with patch.object(reflector, "_load_recent_failures", return_value=[]):
            result_path = reflector.generate_proposal(signal, base)

        assert result_path is not None
        content = (Path(result_path) / "proposal.md").read_text(encoding="utf-8")
        assert "## Past Failures" not in content
