"""Tests for spec: verify-failure-observability

Tests that verify PhaseRecord captures diagnostic detail for all outcomes.
"""
import json
import os
import tempfile

from dataclasses import asdict

from zsiga.metrics.types import ChangeRecord, PhaseRecord, Phase, Outcome


class TestPhaseRecordDetail:
    """Verify that PhaseRecord for verify phase captures meaningful detail."""

    def test_verify_fail_record_has_detail(self):
        """Scenario: Verify fail with verdict detail captured.

        A verify PhaseRecord with outcome=fail MUST have non-empty detail.
        """
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            seconds_used=10.0,
            fix_attempts=0,
            detail="verdict=FAIL; Layer 1: FAIL — 2 testable scenarios",
        )
        assert rec.detail != ""
        assert "FAIL" in rec.detail

    def test_verify_reverted_record_has_detail(self):
        """Scenario: Verify revert captures eval-fix failure reason.

        A reverted verify PhaseRecord MUST contain eval-fix info.
        """
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            seconds_used=10.0,
            fix_attempts=3,
            detail="eval-fix exhausted 3 attempts",
        )
        assert rec.detail != ""
        assert "eval-fix" in rec.detail
        assert "3" in rec.detail

    def test_verify_precheck_failure_has_error_type(self):
        """Scenario: Verify precheck failure captures error type and file.

        A precheck-failure verify PhaseRecord MUST contain both error type
        and file path.
        """
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            seconds_used=0.0,
            fix_attempts=0,
            detail="pre-check: import in zsiga/foo.py",
        )
        assert "import" in rec.detail
        assert "zsiga/foo.py" in rec.detail

    def test_verify_success_record_has_verdict(self):
        """Scenario: Verify success records verdict and layer-1 summary.

        A successful verify PhaseRecord SHOULD contain the verdict string.
        """
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.SUCCESS,
            seconds_used=5.0,
            fix_attempts=0,
            detail="verdict=PASS; Layer 1: PASS — 3 testable scenarios",
        )
        assert "PASS" in rec.detail

    def test_phase_record_serializes_detail_via_change_record(self):
        """PhaseRecord detail is preserved through ChangeRecord.to_dict()."""
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            seconds_used=10.0,
            detail="lint: E701 in foo.py",
        )
        cr = ChangeRecord(
            change_name="test-change",
            project="zsiga",
            outcome=Outcome.REVERTED,
            phases=[rec],
        )
        d = cr.to_dict()
        phase_dict = d["phases"][0]
        assert phase_dict["detail"] == "lint: E701 in foo.py"


class TestVerifyDetailCapture:
    """Test that the verify verdict reader produces usable detail strings."""

    def test_read_verdict_parses_pass(self):
        """read_verdict returns PASS from properly formatted verify.md."""
        from zsiga.pipeline.verifier import read_verdict
        from zsiga.transport import LocalTransport

        with tempfile.TemporaryDirectory() as td:
            verify_path = os.path.join(td, "verify.md")
            with open(verify_path, "w") as f:
                f.write("Verdict: PASS\nLayer 1: PASS — 1 testable scenario\n")

            verdict = read_verdict(td, transport=LocalTransport())
            assert verdict == "PASS"

    def test_read_verdict_parses_fail(self):
        """read_verdict returns FAIL from properly formatted verify.md."""
        from zsiga.pipeline.verifier import read_verdict
        from zsiga.transport import LocalTransport

        with tempfile.TemporaryDirectory() as td:
            verify_path = os.path.join(td, "verify.md")
            with open(verify_path, "w") as f:
                f.write("Verdict: FAIL\nLayer 1: FAIL — 2 testable scenarios failed\n")

            verdict = read_verdict(td, transport=LocalTransport())
            assert verdict == "FAIL"

    def test_read_verdict_returns_unknown_on_missing_file(self):
        """read_verdict returns UNKNOWN when verify.md does not exist."""
        from zsiga.pipeline.verifier import read_verdict
        from zsiga.transport import LocalTransport

        with tempfile.TemporaryDirectory() as td:
            verdict = read_verdict(td, transport=LocalTransport())
            assert verdict == "UNKNOWN"
