"""Tests for spec: reflector-stuck-detection.

Verifies _is_stuck() stuck detection, diagnosis.md generation,
and should_propose() integration.
"""

import json
from datetime import datetime, timedelta
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


# ── Scenario: stuck-when-three-consecutive-fails ─────────────

class TestIsStuckThreeConsecutiveFails:
    """_is_stuck returns True when last 3 matching changes all reverted."""

    def test_three_reverted_returns_true(self, reflector, base):
        changes = [
            _make_change("auto-metric_degradation-verify_pass_rate-20260521", "reverted",
                         _make_verify_fail_phases("lint error")),
            _make_change("auto-metric_degradation-verify_pass_rate-20260521-2", "reverted",
                         _make_verify_fail_phases("test failed")),
            _make_change("auto-metric_degradation-verify_pass_rate-20260521-3", "reverted",
                         _make_verify_fail_phases("import error")),
        ]
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._is_stuck(base, signal)
        assert result is True

    def test_three_reverted_with_mixed_pattern_returns_false(self, reflector, base):
        """Only changes matching the pattern_key should count."""
        changes = [
            _make_change("auto-metric_degradation-verify_pass_rate-20260521", "reverted"),
            _make_change("auto-metric_degradation-success_rate-20260521", "reverted"),
            _make_change("auto-metric_degradation-verify_pass_rate-20260521-2", "reverted"),
        ]
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._is_stuck(base, signal)
        # Only 2 matching → not stuck
        assert result is False


# ── Scenario: not-stuck-when-fewer-than-three-fails ──────────

class TestIsStuckFewerThanThree:
    """_is_stuck returns False when fewer than 3 matching reverted changes."""

    def test_two_reverted_returns_false(self, reflector, base):
        changes = [
            _make_change("auto-metric_degradation-verify_pass_rate-20260521", "reverted"),
            _make_change("auto-metric_degradation-verify_pass_rate-20260521-2", "reverted"),
        ]
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._is_stuck(base, signal)
        assert result is False

    def test_zero_changes_returns_false(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        with patch.object(reflector, "_load_recent_changes", return_value=[]):
            result = reflector._is_stuck(base, signal)
        assert result is False


# ── Scenario: not-stuck-when-mixed-outcomes ───────────────────

class TestIsStuckMixedOutcomes:
    """_is_stuck returns False when matching changes have mixed outcomes."""

    def test_one_success_breaks_streak(self, reflector, base):
        changes = [
            _make_change("auto-metric_degradation-verify_pass_rate-001", "reverted"),
            _make_change("auto-metric_degradation-verify_pass_rate-002", "success"),
            _make_change("auto-metric_degradation-verify_pass_rate-003", "reverted"),
        ]
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            result = reflector._is_stuck(base, signal)
        assert result is False


# ── Scenario: diagnosis-md-created-on-stuck ──────────────────

class TestDiagnosisMdCreatedOnStuck:
    """When stuck, _generate_stuck_diagnosis creates diagnosis.md (not proposal.md)."""

    def test_creates_diagnosis_directory(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Stuck test",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        failures = [
            {"change_name": "auto-metric-verify_pass_rate-001", "fail_reason": "lint error"},
            {"change_name": "auto-metric-verify_pass_rate-002", "fail_reason": "test fail"},
            {"change_name": "auto-metric-verify_pass_rate-003", "fail_reason": "import error"},
        ]
        result_path = reflector._generate_stuck_diagnosis(base, signal, failures)
        assert result_path is not None

        diag_dir = Path(result_path)
        assert diag_dir.exists()
        assert diag_dir.name.startswith("auto-stuck-")
        assert (diag_dir / "diagnosis.md").exists()
        # No proposal.md in stuck directory
        assert not (diag_dir / "proposal.md").exists()

    def test_diagnosis_md_contains_pattern_key(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Stuck test",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        failures = [
            {"change_name": "auto-metric-verify_pass_rate-001", "fail_reason": "lint error"},
        ]
        result_path = reflector._generate_stuck_diagnosis(base, signal, failures)
        content = (Path(result_path) / "diagnosis.md").read_text(encoding="utf-8")
        assert "verify_pass_rate" in content.lower() or "verify-pass-rate" in content.lower()


# ── Scenario: diagnosis-md-lists-failed-changes ──────────────

class TestDiagnosisMdListsFailedChanges:
    """diagnosis.md lists each failed change name and has Recommendation section."""

    def test_lists_failed_change_names(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Stuck test",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        failures = [
            {"change_name": "auto-metric-verify_pass_rate-001", "fail_reason": "lint error"},
            {"change_name": "auto-metric-verify_pass_rate-002", "fail_reason": "test fail"},
        ]
        result_path = reflector._generate_stuck_diagnosis(base, signal, failures)
        content = (Path(result_path) / "diagnosis.md").read_text(encoding="utf-8")

        assert "auto-metric-verify_pass_rate-001" in content
        assert "auto-metric-verify_pass_rate-002" in content

    def test_has_recommendation_section(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Stuck test",
            data={"metric": "verify_pass_rate", "value": 20},
        )
        failures = [
            {"change_name": "auto-metric-verify_pass_rate-001", "fail_reason": "lint error"},
        ]
        result_path = reflector._generate_stuck_diagnosis(base, signal, failures)
        content = (Path(result_path) / "diagnosis.md").read_text(encoding="utf-8")
        assert "## Recommendation" in content
        assert "human" in content.lower() or "intervention" in content.lower()


# ── Scenario: should-propose-rejects-stuck-signal ─────────────

class TestShouldProposeRejectsStuck:
    """should_propose returns False when _is_stuck is True."""

    def test_should_propose_false_when_stuck(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        # Mock _is_stuck to return True, bypassing other checks
        with patch.object(reflector, "_has_external_proposals", return_value=False), \
             patch.object(reflector, "_rate_limit_reached", return_value=False), \
             patch.object(reflector, "_is_duplicate", return_value=False), \
             patch.object(reflector, "_is_stuck", return_value=True):
            result = reflector.should_propose(signal, base)
        assert result is False

    def test_should_propose_true_when_not_stuck(self, reflector, base):
        signal = Signal(
            type="metric_degradation",
            priority="high",
            pattern_key="verify_pass_rate",
            title="Test",
        )
        with patch.object(reflector, "_has_external_proposals", return_value=False), \
             patch.object(reflector, "_rate_limit_reached", return_value=False), \
             patch.object(reflector, "_is_duplicate", return_value=False), \
             patch.object(reflector, "_is_stuck", return_value=False):
            result = reflector.should_propose(signal, base)
        assert result is True
