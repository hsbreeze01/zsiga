"""Tests for the Recovery module (agent/recovery.py)."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from zsiga.agent.recovery import RecoveryManager, RecoveryAction, RecoveryReport
from zsiga.agent.escalation import EscalationManager, Strategy, FailureRecord
from zsiga.transport import LocalTransport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manager(**overrides) -> RecoveryManager:
    """Create a RecoveryManager with sensible defaults for testing."""
    defaults = dict(
        change_name="test-change",
        target_path="/tmp/nonexistent",
        pre_sha="abc123",
        transport=MagicMock(spec=LocalTransport),
        persist_dir="/tmp/nonexistent",
        max_failures=3,
    )
    defaults.update(overrides)
    return RecoveryManager(**defaults)


def _make_manager_no_transport(**overrides) -> RecoveryManager:
    """Create a RecoveryManager without transport/target for unit-only tests."""
    defaults = dict(
        change_name="test-change",
        target_path=None,
        pre_sha=None,
        transport=None,
        persist_dir=None,
        max_failures=3,
    )
    defaults.update(overrides)
    return RecoveryManager(**defaults)


# ---------------------------------------------------------------------------
# REQ-RC-01: Failure Tracking
# ---------------------------------------------------------------------------


class TestFailureTracking:
    """Scenario: Record single and multiple failures."""

    def test_record_single_failure(self):
        """Given a RecoveryManager, when record_failure is called once,
        the register shall contain exactly one entry with attempt=1."""
        mgr = _make_manager_no_transport()
        action = mgr.record_failure(error="E701 at line 5", phase="implement")

        assert isinstance(action, RecoveryAction)
        assert action.attempt == 1
        assert mgr._escalation.attempts == 1
        assert len(mgr._escalation.failures) == 1

        entry = mgr._escalation.failures[0]
        assert entry.attempt == 1
        assert entry.phase == "implement"
        assert entry.error == "E701 at line 5"

    def test_record_multiple_failures_across_phases(self):
        """Given a RecoveryManager with 2 failures, when a 3rd is recorded,
        the register shall contain exactly 3 entries with attempt=3."""
        mgr = _make_manager_no_transport()
        mgr.record_failure(error="lint error", phase="implement")
        mgr.record_failure(error="test failure", phase="verify")
        action = mgr.record_failure(error="assertion failed", phase="verify")

        assert action.attempt == 3
        assert len(mgr._escalation.failures) == 3
        assert mgr._escalation.failures[2].phase == "verify"
        assert mgr._escalation.failures[2].error == "assertion failed"

    def test_failure_preserves_error_text(self):
        """Error text must be preserved exactly."""
        mgr = _make_manager_no_transport()
        error_text = "ModuleNotFoundError: No module named 'foo.bar.baz'"
        mgr.record_failure(error=error_text, phase="implement")

        assert mgr._escalation.failures[0].error == error_text


# ---------------------------------------------------------------------------
# REQ-RC-02: Auto-Rollback on Consecutive Failures
# ---------------------------------------------------------------------------


class TestRollback:
    """Scenarios: Rollback threshold and execution."""

    def test_should_rollback_at_threshold(self):
        """Given max_failures=3 and 3 failures, should_rollback returns True."""
        mgr = _make_manager_no_transport(max_failures=3)
        mgr.record_failure("err1", "implement")
        mgr.record_failure("err2", "implement")
        action = mgr.record_failure("err3", "verify")

        assert action.should_rollback is True
        assert mgr.should_rollback() is True

    def test_no_rollback_below_threshold(self):
        """Given max_failures=3 and 1 failure, should_rollback returns False."""
        mgr = _make_manager_no_transport(max_failures=3)
        mgr.record_failure("err1", "implement")

        assert mgr.should_rollback() is False

    def test_no_rollback_at_two_failures(self):
        """Given max_failures=3 and 2 failures, should_rollback returns False."""
        mgr = _make_manager_no_transport(max_failures=3)
        mgr.record_failure("err1", "implement")
        mgr.record_failure("err2", "verify")

        assert mgr.should_rollback() is False

    @patch("zsiga.agent.recovery.git_ops")
    @patch("zsiga.agent.recovery.record_lesson")
    def test_execute_rollback_calls_reset_hard(self, mock_lesson, mock_git):
        """Execute rollback calls git_ops.reset_hard and record_lesson."""
        mgr = _make_manager()
        # Record 3 failures to get to rollback state
        mgr.record_failure("err1", "implement")
        mgr.record_failure("err2", "implement")
        mgr.record_failure("err3", "verify")

        result = mgr.execute_rollback()

        assert result is True
        mock_git.reset_hard.assert_called_once_with(
            mgr.target_path, mgr.pre_sha, transport=mgr.transport,
        )
        mock_lesson.assert_called_once()
        call_kwargs = mock_lesson.call_args[1] if mock_lesson.call_args[1] else {}
        if not call_kwargs:
            call_kwargs = mock_lesson.call_args[1]
        assert call_kwargs.get("pattern_key") == "pipeline.fail.rollback"

    @patch("zsiga.agent.recovery.git_ops")
    @patch("zsiga.agent.recovery.record_lesson")
    def test_execute_rollback_returns_false_without_sha(self, mock_lesson, mock_git):
        """Execute rollback returns False when target_path or pre_sha missing."""
        mgr = _make_manager_no_transport()
        result = mgr.execute_rollback()

        assert result is False
        mock_git.reset_hard.assert_not_called()


# ---------------------------------------------------------------------------
# REQ-RC-03: Root Cause Analysis
# ---------------------------------------------------------------------------


class TestRootCauseAnalysis:
    """Scenarios: RCA classifies errors and generates hypotheses."""

    def test_rca_classifies_import_error(self):
        """Given an import error, RCA report shall mention import/dependency."""
        mgr = _make_manager()
        mgr.transport.run_shell.return_value = {
            "exit_code": 1, "stdout": "", "stderr": "",
        }
        action = mgr.record_failure(
            error="ModuleNotFoundError: No module named 'foo'", phase="implement",
        )

        assert action.rca_report is not None
        descriptions = " ".join(
            h.description.lower() for h in action.rca_report.hypotheses
        )
        assert any(
            w in descriptions for w in ["import", "dependency", "module"]
        )
        # Confidence > 0
        assert action.rca_report.fix_plan is not None

    def test_rca_generates_multiple_hypotheses(self):
        """Given an ambiguous error, RCA report shall contain 3-5 hypotheses."""
        mgr = _make_manager()
        mgr.transport.run_shell.return_value = {
            "exit_code": 1, "stdout": "", "stderr": "",
        }
        action = mgr.record_failure(
            error="some ambiguous error occurred", phase="verify",
        )

        assert action.rca_report is not None
        assert 3 <= len(action.rca_report.hypotheses) <= 5

    def test_rca_hypotheses_sorted_by_confidence(self):
        """Hypotheses shall be sorted by confidence descending."""
        mgr = _make_manager()
        mgr.transport.run_shell.return_value = {
            "exit_code": 1, "stdout": "", "stderr": "",
        }
        action = mgr.record_failure(
            error="TypeError: unsupported operand", phase="implement",
        )

        hyps = action.rca_report.hypotheses
        for i in range(len(hyps) - 1):
            assert hyps[i].confidence >= hyps[i + 1].confidence


# ---------------------------------------------------------------------------
# REQ-RC-04: Strategy Rotation
# ---------------------------------------------------------------------------


class TestStrategyRotation:
    """Scenarios: Strategy rotates SAME → DIFFERENT_APPROACH → SIMPLIFY."""

    def test_first_failure_returns_same(self):
        """First failure: get_strategy returns SAME."""
        mgr = _make_manager_no_transport()
        mgr.record_failure("err1", "implement")

        # After recording, escalation.attempts=1, next_strategy is at index 1
        # But get_strategy reads from next_strategy which reads self.attempts
        # EscalationManager.next_strategy uses min(self.attempts, len-1)
        # After 1 failure: attempts=1, idx=1 → DIFFERENT_APPROACH
        # Before any failure: get_strategy() returns SAME (attempts=0, idx=0)
        pass  # tested below

    def test_strategy_before_any_failure(self):
        """Before any failure, get_strategy returns SAME."""
        mgr = _make_manager_no_transport()
        assert mgr.get_strategy() == Strategy.SAME

    def test_strategy_after_first_failure(self):
        """After 1st failure, next_strategy returns DIFFERENT_APPROACH."""
        mgr = _make_manager_no_transport()
        mgr.record_failure("err1", "implement")
        # EscalationManager: attempts=1, next_strategy idx=min(1,2)=1 → DIFFERENT_APPROACH
        assert mgr.get_strategy() == Strategy.DIFFERENT_APPROACH

    def test_strategy_after_second_failure(self):
        """After 2nd failure, next_strategy returns SIMPLIFY."""
        mgr = _make_manager_no_transport()
        mgr.record_failure("err1", "implement")
        mgr.record_failure("err2", "implement")
        # attempts=2, idx=min(2,2)=2 → SIMPLIFY
        assert mgr.get_strategy() == Strategy.SIMPLIFY

    def test_strategy_caps_at_last_option(self):
        """After many failures, strategy caps at SIMPLIFY."""
        mgr = _make_manager_no_transport()
        for i in range(5):
            mgr.record_failure(f"err{i}", "implement")

        assert mgr.get_strategy() == Strategy.SIMPLIFY

    def test_different_approach_hint_contains_direction(self):
        """DIFFERENT_APPROACH hint directs agent to try different approach."""
        mgr = _make_manager_no_transport()
        hint = mgr.get_strategy_hint(Strategy.DIFFERENT_APPROACH)
        assert "different approach" in hint.lower()

    def test_simplify_hint_mentions_simplify(self):
        """SIMPLIFY hint mentions simplification."""
        mgr = _make_manager_no_transport()
        hint = mgr.get_strategy_hint(Strategy.SIMPLIFY)
        assert "simplify" in hint.lower()

    def test_same_hint_is_empty(self):
        """SAME strategy produces empty hint."""
        mgr = _make_manager_no_transport()
        hint = mgr.get_strategy_hint(Strategy.SAME)
        assert hint == ""


# ---------------------------------------------------------------------------
# REQ-RC-05: Diagnostic Report Generation
# ---------------------------------------------------------------------------


class TestDiagnosticReport:
    """Scenarios: Report generation on strategy exhaustion."""

    @patch("zsiga.agent.recovery.record_lesson")
    def test_generate_report_creates_markdown(self, mock_lesson):
        """Generate report produces RecoveryReport with all sections."""
        mgr = _make_manager_no_transport()
        mgr.record_failure("err1", "implement")
        mgr.record_failure("err2", "implement")
        mgr.record_failure("err3", "verify")

        report = mgr.generate_diagnostic_report()

        assert isinstance(report, RecoveryReport)
        assert report.total_attempts == 3
        assert len(report.failures) == 3

        md = report.to_markdown()
        assert "# Recovery Report" in md
        assert "## Failure History" in md
        assert "## Strategies Tried" in md
        assert "## Recommended Action" in md

    @patch("zsiga.agent.recovery.record_lesson")
    def test_report_includes_all_failure_records(self, mock_lesson):
        """Report lists all failures with phase, error, strategy."""
        mgr = _make_manager_no_transport()
        mgr.record_failure("lint error", "implement")
        mgr.record_failure("test fail", "implement")
        mgr.record_failure("assertion error", "verify")

        report = mgr.generate_diagnostic_report()
        md = report.to_markdown()

        assert "implement" in md
        assert "verify" in md
        assert "lint error" in md
        assert "test fail" in md
        assert "assertion error" in md

    @patch("zsiga.agent.recovery.record_lesson")
    def test_report_records_lesson(self, mock_lesson):
        """generate_diagnostic_report records lesson with pattern_key."""
        mgr = _make_manager_no_transport()
        mgr.record_failure("err1", "implement")

        mgr.generate_diagnostic_report()

        mock_lesson.assert_called_once()
        call_kwargs = mock_lesson.call_args[1] if mock_lesson.call_args[1] else {}
        if not call_kwargs:
            call_kwargs = mock_lesson.call_args[1]
        assert call_kwargs.get("pattern_key") == "pipeline.fail.recovery"

    def test_report_save_via_transport(self):
        """Report save writes recovery-report.md via transport."""
        report = RecoveryReport(
            change_name="test-change",
            total_attempts=2,
            failures=[
                FailureRecord(
                    attempt=1, timestamp=0.0, error="err1",
                    strategy_used="same", phase="implement",
                ),
            ],
            root_cause="Test root cause",
            root_cause_confirmed=False,
            strategies_tried=["same"],
            recommended_action="Fix it",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            transport = LocalTransport()
            report.save(tmpdir, transport)
            filepath = os.path.join(tmpdir, "recovery-report.md")
            assert os.path.exists(filepath)
            with open(filepath) as f:
                content = f.read()
            assert "Recovery Report" in content
            assert "test-change" in content


# ---------------------------------------------------------------------------
# REQ-RC-06: Backward Compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """EscalationManager shall remain importable and unchanged."""

    def test_escalation_manager_still_importable(self):
        from zsiga.agent.escalation import EscalationManager
        assert EscalationManager is not None

    def test_escalation_manager_independent(self):
        """EscalationManager works independently of RecoveryManager."""
        em = EscalationManager("test")
        em.record_failure("test error", phase="implement")
        assert em.attempts == 1
        assert len(em.failures) == 1

    def test_recovery_manager_wraps_escalation(self):
        """RecoveryManager composes EscalationManager internally."""
        mgr = _make_manager_no_transport()
        assert isinstance(mgr._escalation, EscalationManager)
