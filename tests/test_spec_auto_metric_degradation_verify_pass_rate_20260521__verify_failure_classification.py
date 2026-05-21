"""Tests for spec: verify-failure-classification

Tests that verify failures are classified into categories and reported.
"""
import json
import tempfile

from zsiga.metrics.types import PhaseRecord, Phase, Outcome


class TestClassifyVerifyFailure:
    """Test the classify_verify_failure function."""

    def test_classify_lint_failure(self):
        """Scenario: Classify lint failure.

        verify.md with E701 and lint failure → 'lint'.
        """
        from zsiga.pipeline.verifier import classify_verify_failure

        verify_md = (
            "Verdict: FAIL\n"
            "Layer 1: PASS — 0 testable scenarios\n"
            "Issues:\n"
            "  1. [CRITICAL] lint: E701 Multiple statements on one line\n"
        )
        result = classify_verify_failure(
            verify_md,
            mech_results={"test": {"passed": True}, "lint": {"passed": False}},
        )
        assert result == "lint"

    def test_classify_test_failure(self):
        """Scenario: Classify test failure.

        verify.md with FAILED test → 'test'.
        """
        from zsiga.pipeline.verifier import classify_verify_failure

        verify_md = (
            "Verdict: FAIL\n"
            "Layer 1: FAIL — 2 testable scenarios\n"
            "Issues:\n"
            "  1. [CRITICAL] FAILED test_foo.py::test_bar\n"
        )
        result = classify_verify_failure(
            verify_md,
            mech_results={"test": {"passed": False}, "lint": {"passed": True}},
        )
        assert result == "test"

    def test_classify_layer1_pytest_failure(self):
        """Scenario: Classify layer1_pytest failure.

        verify_layer1.json with passed=false → 'layer1_pytest'.
        """
        from zsiga.pipeline.verifier import classify_verify_failure

        verify_md = "Verdict: FAIL\nLayer 1: FAIL — 2 testable scenarios\n"
        result = classify_verify_failure(
            verify_md,
            layer1_result={"passed": False, "vacuous": False},
        )
        assert result == "layer1_pytest"

    def test_classify_unknown_when_no_content(self):
        """Scenario: Classify unknown when no verify.md.

        Empty verify.md content and no mech_results → 'unknown'.
        """
        from zsiga.pipeline.verifier import classify_verify_failure

        result = classify_verify_failure("")
        assert result == "unknown"

    def test_classify_llm_judge_when_no_mechanical_failure(self):
        """LLM wrote FAIL but no mechanical check failed → 'llm_judge'."""
        from zsiga.pipeline.verifier import classify_verify_failure

        verify_md = (
            "Verdict: FAIL\n"
            "Layer 1: vacuous\n"
            "Completeness: ✗ spec requires logging but no logging added\n"
        )
        result = classify_verify_failure(
            verify_md,
            mech_results={"test": {"passed": True}, "lint": {"passed": True}},
        )
        assert result == "llm_judge"

    def test_classify_precheck_import(self):
        """precheck error type import → 'precheck_import'."""
        from zsiga.pipeline.verifier import classify_verify_failure

        verify_md = "Verdict: FAIL\nPre-check failure (import):\n"
        result = classify_verify_failure(
            verify_md,
            precheck_error_type="import",
        )
        assert result == "precheck_import"


class TestFailureCategoryInPhaseRecord:
    """Test that PhaseRecord supports failure_category field."""

    def test_phase_record_with_failure_category(self):
        """Scenario: Failure category recorded in PhaseRecord."""
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            seconds_used=10.0,
            failure_category="lint",
        )
        d = rec.to_dict()
        assert "failure_category" in d
        assert d["failure_category"] == "lint"

    def test_phase_record_without_failure_category(self):
        """PhaseRecord without failure_category serializes without error."""
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.SUCCESS,
            seconds_used=5.0,
        )
        d = rec.to_dict()
        # Should not crash; failure_category may be absent or None
        assert d.get("failure_category") is None or "failure_category" not in d


class TestVerifyFailureBreakdown:
    """Test that compute_stats reports verify failure breakdown."""

    def test_compute_stats_reports_breakdown(self):
        """Scenario: Verify failure breakdown in stats output."""
        from zsiga.metrics.collector import compute_stats

        changes = [
            {
                "change_name": "test-1",
                "project": "zsiga",
                "outcome": "reverted",
                "started_at": "2026-01-01T00:00:00",
                "finished_at": "2026-01-01T01:00:00",
                "phases": [
                    {
                        "phase": "verify",
                        "outcome": "fail",
                        "seconds_used": 10,
                        "failure_category": "lint",
                    },
                ],
            },
            {
                "change_name": "test-2",
                "project": "zsiga",
                "outcome": "reverted",
                "started_at": "2026-01-01T02:00:00",
                "finished_at": "2026-01-01T03:00:00",
                "phases": [
                    {
                        "phase": "verify",
                        "outcome": "fail",
                        "seconds_used": 10,
                        "failure_category": "lint",
                    },
                ],
            },
            {
                "change_name": "test-3",
                "project": "zsiga",
                "outcome": "reverted",
                "started_at": "2026-01-01T04:00:00",
                "finished_at": "2026-01-01T05:00:00",
                "phases": [
                    {
                        "phase": "verify",
                        "outcome": "fail",
                        "seconds_used": 10,
                        "failure_category": "test",
                    },
                ],
            },
        ]

        stats = compute_stats(changes)
        assert "verify_failure_breakdown" in stats
        breakdown = stats["verify_failure_breakdown"]
        assert breakdown.get("lint") == 2
        assert breakdown.get("test") == 1
