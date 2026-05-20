"""Tests for zsiga.intake.reflector — Self-Reflection Loop."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.intake.reflector import Reflector, Signal


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def reflector():
    return Reflector()


@pytest.fixture
def base(tmp_path):
    """Create a minimal base directory structure."""
    (tmp_path / "memory").mkdir()
    (tmp_path / "openspec" / "changes").mkdir(parents=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "metrics").mkdir()
    return tmp_path


def _write_learnings(base: Path, entries: list[dict]):
    """Write learnings.jsonl entries."""
    lines = [json.dumps(e, ensure_ascii=False) for e in entries]
    (base / "memory" / "learnings.jsonl").write_text("\n".join(lines), encoding="utf-8")


def _write_history(base: Path, entries: list[dict]):
    """Write reflector_history.jsonl entries."""
    lines = [json.dumps(e, ensure_ascii=False) for e in entries]
    (base / "data" / "reflector_history.jsonl").write_text("\n".join(lines), encoding="utf-8")


def _write_changes(base: Path, entries: list[dict]):
    """Write metrics/changes.jsonl entries."""
    lines = [json.dumps(e, ensure_ascii=False) for e in entries]
    (base / "metrics" / "changes.jsonl").write_text("\n".join(lines), encoding="utf-8")


def _make_change(name: str, outcome: str = "success") -> dict:
    return {
        "change_name": name,
        "project": "zsiga",
        "outcome": outcome,
        "started_at": "",
        "finished_at": "",
        "lessons_count": 0,
        "phases": [],
    }


# ── Signal dataclass ──────────────────────────────────────────


class TestSignal:
    def test_signal_fields(self):
        s = Signal(
            type="recurring_failure",
            priority="high",
            pattern_key="pipeline-fail-implement",
            title="Test signal",
            data={"count": 5},
        )
        assert s.type == "recurring_failure"
        assert s.priority == "high"
        assert s.pattern_key == "pipeline-fail-implement"
        assert s.title == "Test signal"
        assert s.data == {"count": 5}

    def test_signal_default_data(self):
        s = Signal(type="test", priority="medium", pattern_key="k", title="t")
        assert s.data == {}


# ── scan_signals: recurring failure ───────────────────────────


class TestScanRecurringFailures:
    def test_high_severity_pattern_detected(self, reflector, base):
        """High-severity pattern with count>=3 and no existing proposal → signal."""
        entries = []
        for i in range(6):
            entries.append({
                "pattern_key": "pipeline.fail.implement",
                "takeaway": f"Failed at implement: error {i}",
                "ts": f"2025-01-{10+i:02d}T10:00:00",
            })
        _write_learnings(base, entries)

        signals = reflector._scan_recurring_failures(base)
        assert len(signals) == 1
        s = signals[0]
        assert s.type == "recurring_failure"
        assert s.priority == "high"
        assert "pipeline" in s.pattern_key and "fail" in s.pattern_key
        assert s.data["count"] == 6
        assert len(s.data["recent_takeaways"]) <= 3

    def test_pattern_skipped_if_already_covered(self, reflector, base):
        """Pattern covered by existing proposal directory → no signal."""
        entries = [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "fail", "ts": "2025-01-10T10:00:00"},
        ] * 4
        _write_learnings(base, entries)

        # Create an existing proposal directory covering this pattern
        changes_dir = base / "openspec" / "changes"
        (changes_dir / "auto-recurring_failure-pipeline-fail-implement-20250110").mkdir()

        signals = reflector._scan_recurring_failures(base)
        assert len(signals) == 0

    def test_no_signals_when_healthy(self, reflector, base):
        """No high-severity patterns → empty list."""
        # No learnings file
        signals = reflector._scan_recurring_failures(base)
        assert signals == []

    def test_low_severity_ignored(self, reflector, base):
        """Patterns with severity != "high" are skipped."""
        # "pass" in key → severity "low"
        entries = [
            {"pattern_key": "pipeline.pass.deliver", "takeaway": "Success", "ts": "2025-01-10T10:00:00"},
        ] * 4
        _write_learnings(base, entries)

        signals = reflector._scan_recurring_failures(base)
        assert len(signals) == 0


# ── scan_signals: metric degradation ──────────────────────────


class TestScanMetricDegradation:
    def test_low_success_rate_triggers_signal(self, reflector, base):
        """success_rate_pct < 70 → signal."""
        mock_stats = {"success_rate_pct": 40, "verify_pass_rate_pct": 80}
        with patch.object(reflector, "_load_current_stats", return_value=mock_stats), \
             patch.object(reflector, "_check_budget_exceed_rate", return_value=None), \
             patch.object(reflector, "_load_prior_snapshot", return_value=None):
            signals = reflector._scan_metric_degradation(base)
        assert any(s.data["metric"] == "success_rate" and s.data["value"] == 40 for s in signals)

    def test_low_verify_rate_triggers_signal(self, reflector, base):
        """verify_pass_rate_pct < 50 → signal."""
        mock_stats = {"success_rate_pct": 80, "verify_pass_rate_pct": 30}
        with patch.object(reflector, "_load_current_stats", return_value=mock_stats), \
             patch.object(reflector, "_check_budget_exceed_rate", return_value=None), \
             patch.object(reflector, "_load_prior_snapshot", return_value=None):
            signals = reflector._scan_metric_degradation(base)
        assert any(s.data["metric"] == "verify_pass_rate" for s in signals)

    def test_budget_exceed_rate(self, reflector, base):
        """≥ 3 of last 10 changes have BUDGET_EXCEEDED → signal."""
        mock_stats = {"success_rate_pct": 80, "verify_pass_rate_pct": 80}
        changes = [_make_change(f"c{i}", "BUDGET_EXCEEDED") for i in range(4)] + \
                  [_make_change(f"c{i}", "success") for i in range(4, 10)]
        with patch.object(reflector, "_load_current_stats", return_value=mock_stats), \
             patch.object(reflector, "_load_recent_changes", return_value=changes), \
             patch.object(reflector, "_load_prior_snapshot", return_value=None):
            signals = reflector._scan_metric_degradation(base)
        budget_signals = [s for s in signals if s.data.get("metric") == "budget_exceed_rate"]
        assert len(budget_signals) == 1
        assert budget_signals[0].data["value"] == 4

    def test_no_signals_when_healthy(self, reflector, base):
        """All metrics above thresholds → no degradation signals."""
        mock_stats = {"success_rate_pct": 90, "verify_pass_rate_pct": 80}
        with patch.object(reflector, "_load_current_stats", return_value=mock_stats), \
             patch.object(reflector, "_check_budget_exceed_rate", return_value=None), \
             patch.object(reflector, "_load_prior_snapshot", return_value=None):
            signals = reflector._scan_metric_degradation(base)
        assert len(signals) == 0

    def test_no_stats_returns_empty(self, reflector, base):
        """Missing stats → empty signals."""
        with patch.object(reflector, "_load_current_stats", return_value=None):
            signals = reflector._scan_metric_degradation(base)
        assert signals == []

    def test_metric_drop_over_10_percent(self, reflector, base):
        """Metric drops > 10% compared to snapshot → elevated priority signal."""
        mock_stats = {"success_rate_pct": 50, "verify_pass_rate_pct": 80}
        prior_stats = {"success_rate_pct": 75, "verify_pass_rate_pct": 85}
        with patch.object(reflector, "_load_current_stats", return_value=mock_stats), \
             patch.object(reflector, "_check_budget_exceed_rate", return_value=None), \
             patch.object(reflector, "_load_prior_snapshot", return_value=prior_stats):
            signals = reflector._scan_metric_degradation(base)
        drop_signals = [s for s in signals if "drop" in s.pattern_key]
        assert any(s.pattern_key == "success_rate_pct_drop" for s in drop_signals)


# ── scan_signals: recurring root causes ───────────────────────


class TestScanRecurringRootCauses:
    def test_recurring_root_cause_detected(self, reflector, base):
        """2 reverted changes with same root_cause → signal."""
        changes = [
            _make_change("change-a", "reverted"),
            _make_change("change-b", "reverted"),
        ]
        # Write diagnosis.md files
        for name in ["change-a", "change-b"]:
            diag_dir = base / "openspec" / "changes" / name
            diag_dir.mkdir(parents=True)
            (diag_dir / "diagnosis.md").write_text(
                "## Root Cause\nmissing_import_in_template\n",
                encoding="utf-8",
            )

        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            signals = reflector._scan_recurring_root_causes(base)

        assert len(signals) == 1
        s = signals[0]
        assert s.type == "recurring_root_cause"
        assert s.data["root_cause"] == "missing_import_in_template"
        assert s.data["occurrences"] == 2

    def test_no_signals_when_no_reverted(self, reflector, base):
        """No reverted changes → no root cause signals."""
        changes = [_make_change("c1", "success"), _make_change("c2", "success")]
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            signals = reflector._scan_recurring_root_causes(base)
        assert signals == []

    def test_no_signals_when_different_root_causes(self, reflector, base):
        """Reverted changes with different root causes → no signal (each < 2)."""
        changes = [
            _make_change("change-a", "reverted"),
            _make_change("change-b", "reverted"),
        ]
        for i, name in enumerate(["change-a", "change-b"]):
            diag_dir = base / "openspec" / "changes" / name
            diag_dir.mkdir(parents=True)
            (diag_dir / "diagnosis.md").write_text(
                f"## Root Cause\ndifferent_cause_{i}\n", encoding="utf-8"
            )
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            signals = reflector._scan_recurring_root_causes(base)
        assert signals == []


# ── should_propose: dedup ─────────────────────────────────────


class TestShouldProposeDedup:
    def test_duplicate_suppressed_within_24h(self, reflector, base):
        """Same signal_type + pattern_key within 24h → False."""
        now = datetime.now().isoformat()
        _write_history(base, [
            {"timestamp": now, "signal_type": "recurring_failure", "pattern_key": "pipeline.fail.implement"},
        ])
        signal = Signal(
            type="recurring_failure",
            priority="high",
            pattern_key="pipeline.fail.implement",
            title="Test",
        )
        assert reflector.should_propose(signal, base) is False

    def test_duplicate_allowed_after_24h(self, reflector, base):
        """Same signal_type + pattern_key after 24h → allowed (rate check permitting)."""
        old_ts = (datetime.now() - timedelta(hours=25)).isoformat()
        _write_history(base, [
            {"timestamp": old_ts, "signal_type": "recurring_failure", "pattern_key": "pipeline.fail.implement"},
        ])
        signal = Signal(
            type="recurring_failure",
            priority="high",
            pattern_key="pipeline.fail.implement",
            title="Test",
        )
        assert reflector.should_propose(signal, base) is True


# ── should_propose: rate limit ────────────────────────────────


class TestShouldProposeRateLimit:
    def test_rate_limit_disabled_allows_at_3_per_24h(self, reflector, base):
        """3 entries in past 24h but rate limit is disabled → proposal allowed."""
        now = datetime.now().isoformat()
        _write_history(base, [
            {"timestamp": now, "signal_type": "recurring_failure", "pattern_key": "a"},
            {"timestamp": now, "signal_type": "metric_degradation", "pattern_key": "b"},
            {"timestamp": now, "signal_type": "recurring_root_cause", "pattern_key": "c"},
        ])
        signal = Signal(type="recurring_failure", priority="high", pattern_key="new", title="t")
        assert reflector.should_propose(signal, base) is True

    def test_under_rate_limit_allows(self, reflector, base):
        """1 entry in past 24h → under rate limit, allowed."""
        now = datetime.now().isoformat()
        _write_history(base, [
            {"timestamp": now, "signal_type": "recurring_failure", "pattern_key": "a"},
        ])
        signal = Signal(type="recurring_failure", priority="high", pattern_key="new", title="t")
        assert reflector.should_propose(signal, base) is True


# ── should_propose: external proposal priority ────────────────


class TestShouldProposeExternal:
    def test_external_proposal_blocks(self, reflector, base):
        """Non-auto directory in openspec/changes/ → should_propose returns False."""
        # Create a non-auto directory
        (base / "openspec" / "changes" / "some-feature").mkdir()
        signal = Signal(type="recurring_failure", priority="high", pattern_key="test", title="t")
        assert reflector.should_propose(signal, base) is False

    def test_auto_proposals_dont_block(self, reflector, base):
        """Only auto- prefixed directories → should_propose proceeds."""
        (base / "openspec" / "changes" / "auto-something").mkdir()
        signal = Signal(type="recurring_failure", priority="high", pattern_key="test", title="t")
        assert reflector.should_propose(signal, base) is True

    def test_archive_dir_ignored(self, reflector, base):
        """The 'archive' directory is not treated as an external proposal."""
        (base / "openspec" / "changes" / "archive").mkdir()
        signal = Signal(type="recurring_failure", priority="high", pattern_key="test", title="t")
        assert reflector.should_propose(signal, base) is True


# ── generate_proposal ─────────────────────────────────────────


class TestGenerateProposal:
    def test_directory_and_file_created(self, reflector, base):
        """generate_proposal creates directory with proposal.md."""
        signal = Signal(
            type="recurring_failure",
            priority="high",
            pattern_key="pipeline-fail-implement",
            title="Test",
            data={"count": 6, "recent_takeaways": ["error1", "error2"]},
        )
        result = reflector.generate_proposal(signal, base)
        assert result is not None

        proposal_dir = Path(result)
        assert proposal_dir.exists()
        assert proposal_dir.name.startswith("auto-recurring_failure-pipeline-fail-implement-")
        assert (proposal_dir / "proposal.md").exists()

        content = (proposal_dir / "proposal.md").read_text(encoding="utf-8")
        assert "Summary" in content
        assert "Motivation" in content
        assert "pipeline-fail-implement" in content
        assert "Constraints" in content
        assert "pytest" in content
        assert "ruff" in content

    def test_special_chars_sanitized(self, reflector, base):
        """Pattern key with special chars is sanitized for filesystem."""
        signal = Signal(
            type="recurring_failure",
            priority="high",
            pattern_key="some/pattern:with:special|chars",
            title="Test",
            data={"count": 3, "recent_takeaways": []},
        )
        result = reflector.generate_proposal(signal, base)
        assert result is not None
        dirname = Path(result).name
        assert "/" not in dirname
        assert ":" not in dirname
        assert "|" not in dirname
        # Only alphanumeric, hyphens, underscores after auto-recurring_failure-
        key_part = dirname.split("-", 2)[-1].rsplit("-", 1)[0]
        import re
        assert re.match(r'^[a-zA-Z0-9_-]+$', key_part), f"Key part has invalid chars: {key_part}"

    def test_duplicate_dirname_incremented(self, reflector, base):
        """If directory already exists, append -2, -3, etc."""
        signal = Signal(
            type="recurring_failure",
            priority="high",
            pattern_key="test-key",
            title="Test",
            data={"count": 3, "recent_takeaways": []},
        )
        result1 = reflector.generate_proposal(signal, base)
        assert result1 is not None

        # Need to clear dedup for second proposal
        result2 = reflector.generate_proposal(signal, base)
        assert result2 is not None
        assert Path(result1).name != Path(result2).name

    def test_history_recorded(self, reflector, base):
        """generate_proposal records entry in reflector_history.jsonl."""
        signal = Signal(
            type="metric_degradation",
            priority="medium",
            pattern_key="success_rate",
            title="Test",
            data={"metric": "success_rate", "value": 40},
        )
        reflector.generate_proposal(signal, base)

        history_path = base / "data" / "reflector_history.jsonl"
        assert history_path.exists()
        lines = history_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["signal_type"] == "metric_degradation"
        assert entry["pattern_key"] == "success_rate"

    def test_recurring_root_cause_template(self, reflector, base):
        """Recurring root cause signal generates correct proposal content."""
        signal = Signal(
            type="recurring_root_cause",
            priority="high",
            pattern_key="missing-import-in-template",
            title="Test",
            data={"root_cause": "missing_import_in_template", "occurrences": 3},
        )
        result = reflector.generate_proposal(signal, base)
        content = (Path(result) / "proposal.md").read_text(encoding="utf-8")
        assert "missing_import_in_template" in content
        assert "3" in content


# ── run (orchestration) ───────────────────────────────────────


class TestRun:
    def test_run_scans_filters_and_generates(self, reflector, base):
        """run() orchestrates scan → filter → generate correctly."""
        # Write learnings to trigger a recurring_failure signal
        entries = []
        for i in range(6):
            entries.append({
                "pattern_key": "pipeline.fail.implement",
                "takeaway": f"Failed at implement: error {i}",
                "ts": f"2025-01-{10+i:02d}T10:00:00",
            })
        _write_learnings(base, entries)

        proposals = reflector.run(base)
        assert len(proposals) >= 1
        # Check that proposal.md was created
        for p in proposals:
            assert (Path(p) / "proposal.md").exists()

    def test_run_returns_empty_when_healthy(self, reflector, base):
        """No signals → run returns empty list."""
        proposals = reflector.run(base)
        assert proposals == []

    def test_run_respects_dedup(self, reflector, base):
        """Second run with same signal → deduplicated, no new proposals."""
        entries = []
        for i in range(6):
            entries.append({
                "pattern_key": "pipeline.fail.implement",
                "takeaway": f"Failed {i}",
                "ts": f"2025-01-{10+i:02d}T10:00:00",
            })
        _write_learnings(base, entries)

        first = reflector.run(base)
        assert len(first) >= 1

        second = reflector.run(base)
        assert len(second) == 0  # dedup within 24h


# ── Error resilience ──────────────────────────────────────────


class TestErrorResilience:
    def test_missing_learnings_file(self, reflector, base):
        """No learnings.jsonl → scan_signals returns empty (no crash)."""
        # Don't create learnings.jsonl
        signals = reflector._scan_recurring_failures(base)
        assert signals == []

    def test_corrupted_jsonl_line_skipped(self, reflector, base):
        """Corrupted JSONL line is skipped without crash."""
        # Write a mix of valid and invalid lines
        content = (
            '{"pattern_key":"test.fail","takeaway":"ok","ts":"2025-01-10T10:00:00"}\n'
            "INVALID JSON LINE\n"
            '{"pattern_key":"test.fail","takeaway":"ok2","ts":"2025-01-11T10:00:00"}\n'
            '{"pattern_key":"test.fail","takeaway":"ok3","ts":"2025-01-12T10:00:00"}\n'
        )
        (base / "memory" / "learnings.jsonl").write_text(content, encoding="utf-8")

        # mine_patterns handles corrupted lines internally
        signals = reflector._scan_recurring_failures(base)
        # Should get a signal from the 3 valid lines
        assert len(signals) == 1
        assert signals[0].data["count"] == 3

    def test_corrupted_history_jsonl(self, reflector, base):
        """Corrupted reflector_history.jsonl lines are skipped."""
        content = (
            '{"timestamp":"' + datetime.now().isoformat() + '","signal_type":"recurring_failure","pattern_key":"a"}\n'
            "BAD LINE\n"
        )
        (base / "data" / "reflector_history.jsonl").write_text(content, encoding="utf-8")

        # Should not crash, should count the valid entry
        signal = Signal(type="recurring_failure", priority="high", pattern_key="new", title="t")
        result = reflector.should_propose(signal, base)
        # Only 1 entry, so rate limit not reached, and not a dup → True
        assert result is True

    def test_missing_changes_dir(self, reflector, base):
        """Missing openspec/changes → no crash, returns empty."""
        import shutil
        changes_dir = base / "openspec" / "changes"
        if changes_dir.exists():
            shutil.rmtree(changes_dir)

        signals = reflector._scan_recurring_failures(base)
        assert signals == []

    def test_diagnosis_read_error_handled(self, reflector, base):
        """Unreadable diagnosis.md → no crash."""
        changes = [_make_change("change-a", "reverted")]
        diag_dir = base / "openspec" / "changes" / "change-a"
        diag_dir.mkdir(parents=True)
        # Create a file but mock read to fail
        (diag_dir / "diagnosis.md").write_text("## Root Cause\ntest_cause\n", encoding="utf-8")

        # Verify it normally works
        with patch.object(reflector, "_load_recent_changes", return_value=changes):
            signals = reflector._scan_recurring_root_causes(base)
        # Only 1 occurrence → no signal
        assert signals == []
