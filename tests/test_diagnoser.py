"""Tests for the Diagnoser module."""

import os
import tempfile

from zsiga.pipeline.diagnoser import (
    Diagnoser, Hypothesis, ProbeResult, FixPlan, DiagnosisReport,
    PreCheckResult, verify_precheck,
)
from zsiga.transport import LocalTransport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeTransport(LocalTransport):
    """Transport that tracks whether any write operations occurred."""

    def __init__(self):
        super().__init__()
        self.writes: list[str] = []

    def run_shell(self, cmd: str, cwd=None, timeout=120, stdin_data=None):
        # Track write-like operations
        for pattern in ["write_file", "edit_file", "ast_replace", "rm ", "mv "]:
            if pattern in cmd and "cat >" not in cmd:
                self.writes.append(cmd)
        # For diagnosis.md write, actually do it via parent
        return super().run_shell(cmd, cwd=cwd, timeout=timeout, stdin_data=stdin_data)


# ---------------------------------------------------------------------------
# Task 1.1: Core Diagnoser Module
# ---------------------------------------------------------------------------

class TestDiagnoserImport:
    """Scenario: Diagnoser is importable."""

    def test_import_succeeds(self):
        from zsiga.pipeline.diagnoser import Diagnoser
        assert Diagnoser is not None

    def test_has_required_methods(self):
        d = Diagnoser()
        assert hasattr(d, "hypothesize")
        assert hasattr(d, "instrument")
        assert hasattr(d, "targeted_fix")
        assert callable(d.hypothesize)
        assert callable(d.instrument)
        assert callable(d.targeted_fix)


# ---------------------------------------------------------------------------
# Hypothesis Generation
# ---------------------------------------------------------------------------

class TestHypothesize:
    """Scenarios: Generate hypotheses from verify failure."""

    def test_returns_3_to_5_hypotheses(self):
        d = Diagnoser()
        failure = {"detail": "tests:\nAssertionError at line 42"}
        hyps = d.hypothesize(failure)
        assert 3 <= len(hyps) <= 5

    def test_hypotheses_have_required_fields(self):
        d = Diagnoser()
        failure = {"detail": "tests:\nAssertionError at line 42"}
        hyps = d.hypothesize(failure)
        for h in hyps:
            assert isinstance(h, Hypothesis)
            assert isinstance(h.rank, int)
            assert isinstance(h.description, str)
            assert isinstance(h.confidence, float)
            assert 0.0 <= h.confidence <= 1.0
            assert isinstance(h.evidence, str)

    def test_hypotheses_sorted_by_confidence_descending(self):
        d = Diagnoser()
        failure = {"detail": "tests:\nAssertionError at line 42"}
        hyps = d.hypothesize(failure)
        for i in range(len(hyps) - 1):
            assert hyps[i].confidence >= hyps[i + 1].confidence

    def test_hypotheses_ranks_are_1_based(self):
        d = Diagnoser()
        failure = {"detail": "tests:\nAssertionError at line 42"}
        hyps = d.hypothesize(failure)
        for i, h in enumerate(hyps):
            assert h.rank == i + 1

    def test_import_error_hypothesis_mentions_import(self):
        d = Diagnoser()
        failure = {"detail": "ImportError: No module named 'foo'"}
        hyps = d.hypothesize(failure)
        descriptions = " ".join(h.description.lower() for h in hyps)
        assert any(w in descriptions for w in ["import", "module", "dependency"])

    def test_generic_failure_produces_hypotheses(self):
        d = Diagnoser()
        failure = {"detail": "FAILED test_something - some output"}
        hyps = d.hypothesize(failure)
        assert len(hyps) >= 1

    def test_unknown_error_produces_fallback(self):
        d = Diagnoser()
        failure = {"detail": "something went completely sideways xyz"}
        hyps = d.hypothesize(failure)
        assert len(hyps) >= 1
        descriptions = " ".join(h.description.lower() for h in hyps)
        assert "unknown" in descriptions

    def test_multiple_error_patterns(self):
        d = Diagnoser()
        failure = {"detail": "ImportError: No module named 'foo'\nAssertionError at line 10\nTypeError: unsupported operand"}
        hyps = d.hypothesize(failure)
        descriptions = [h.description.lower() for h in hyps]
        assert any("import" in d or "module" in d or "dependency" in d for d in descriptions)


# ---------------------------------------------------------------------------
# Instrumentation
# ---------------------------------------------------------------------------

class TestInstrument:
    """Scenarios: Instrument probes hypotheses without side effects."""

    def test_instrument_produces_probe_results(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=1, description="Missing or incorrect import",
                       confidence=0.9, evidence="ImportError: No module named 'foo'"),
            Hypothesis(rank=2, description="Test expectation mismatch",
                       confidence=0.8, evidence="AssertionError at line 42"),
            Hypothesis(rank=3, description="Code style or syntax violation",
                       confidence=0.75, evidence="E701 at line 10"),
        ]
        transport = _FakeTransport()
        result = d.instrument(hyps, "/tmp/nonexistent_project", transport)
        probed = [h for h in result if h.probe_result is not None]
        assert len(probed) == 3  # all 3 should be probed (max 3)

    def test_at_most_3_hypotheses_probed(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=i, description=f"hyp {i}",
                       confidence=0.9 - i * 0.1,
                       evidence="some error")
            for i in range(1, 6)
        ]
        transport = _FakeTransport()
        result = d.instrument(hyps, "/tmp/nonexistent_project", transport)
        probed = [h for h in result if h.probe_result is not None]
        assert len(probed) <= 3

    def test_probe_results_have_correct_fields(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=1, description="Missing or incorrect import",
                       confidence=0.9, evidence="ImportError: No module named 'foo'"),
        ]
        transport = _FakeTransport()
        result = d.instrument(hyps, "/tmp/nonexistent_project", transport)
        pr = result[0].probe_result
        assert pr is not None
        assert isinstance(pr, ProbeResult)
        assert isinstance(pr.confirmed, bool)
        assert isinstance(pr.evidence, str)
        assert isinstance(pr.probe_type, str)

    def test_instrument_no_file_modification(self):
        """Instrumentation should not modify any project files."""
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=1, description="Missing or incorrect import",
                       confidence=0.9, evidence="ImportError: No module named 'foo'"),
        ]
        transport = _FakeTransport()
        d.instrument(hyps, "/tmp/nonexistent_project", transport)
        # _FakeTransport only tracks non-cat writes; cat > for diagnosis.md is excluded
        assert len(transport.writes) == 0


# ---------------------------------------------------------------------------
# Targeted Fix Generation
# ---------------------------------------------------------------------------

class TestTargetedFix:
    """Scenarios: Generate fix plan from confirmed hypothesis."""

    def test_confirmed_hypothesis_produces_confirmed_fix(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=1, description="Missing or incorrect import",
                       confidence=0.9, evidence="ImportError",
                       probe_result=ProbeResult(confirmed=False, evidence="no", probe_type="search")),
            Hypothesis(rank=2, description="Test expectation mismatch",
                       confidence=0.8, evidence="AssertionError",
                       probe_result=ProbeResult(confirmed=True, evidence="found it", probe_type="search")),
            Hypothesis(rank=3, description="Unknown",
                       confidence=0.3, evidence=""),
        ]
        plan = d.targeted_fix(hyps)
        assert isinstance(plan, FixPlan)
        assert plan.confirmed is True
        assert "Test expectation mismatch" in plan.root_cause

    def test_no_confirmed_falls_back_to_best_guess(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=1, description="Missing or incorrect import",
                       confidence=0.9, evidence="ImportError: No module named 'xyz'",
                       probe_result=ProbeResult(confirmed=False, evidence="no", probe_type="search")),
            Hypothesis(rank=2, description="Test expectation mismatch",
                       confidence=0.8, evidence="AssertionError",
                       probe_result=ProbeResult(confirmed=False, evidence="nope", probe_type="search")),
        ]
        plan = d.targeted_fix(hyps)
        assert isinstance(plan, FixPlan)
        assert plan.confirmed is False
        assert "Missing or incorrect import" in plan.root_cause
        # Should contain actionable info about the module, NOT generic "Unconfirmed hypothesis"
        assert "unconfirmed hypothesis" not in plan.fix_description.lower()
        assert "needs further investigation" not in plan.fix_description.lower()

    def test_fix_plan_has_required_fields(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(rank=1, description="Test", confidence=0.5, evidence=""),
        ]
        plan = d.targeted_fix(hyps)
        assert isinstance(plan.root_cause, str)
        assert isinstance(plan.fix_description, str)
        assert isinstance(plan.affected_files, list)
        assert isinstance(plan.confirmed, bool)


# ---------------------------------------------------------------------------
# Diagnosis Report
# ---------------------------------------------------------------------------

class TestDiagnosisReport:
    """Scenarios: Diagnosis report is generated and persisted."""

    def test_report_has_required_fields(self):
        report = DiagnosisReport(
            change_name="test-change",
            hypotheses=[
                Hypothesis(rank=1, description="Test hyp", confidence=0.9, evidence="test"),
            ],
            confirmed_hypothesis=None,
            fix_plan=FixPlan(
                root_cause="Test cause",
                fix_description="Fix it",
                affected_files=["test.py"],
                confirmed=False,
            ),
            timestamp="2024-01-01T00:00:00",
        )
        assert report.change_name == "test-change"
        assert len(report.hypotheses) == 1
        assert report.confirmed_hypothesis is None
        assert isinstance(report.fix_plan, FixPlan)
        assert isinstance(report.timestamp, str)

    def test_to_markdown_produces_content(self):
        report = DiagnosisReport(
            change_name="l4-diagnoser",
            hypotheses=[
                Hypothesis(rank=1, description="Missing import",
                           confidence=0.9, evidence="ImportError",
                           probe_result=ProbeResult(confirmed=True, evidence="found", probe_type="search")),
                Hypothesis(rank=2, description="Syntax error",
                           confidence=0.7, evidence="E701",
                           probe_result=ProbeResult(confirmed=False, evidence="not found", probe_type="diagnostics")),
            ],
            confirmed_hypothesis=Hypothesis(rank=1, description="Missing import",
                                            confidence=0.9, evidence="ImportError"),
            fix_plan=FixPlan(
                root_cause="Missing import",
                fix_description="Add the missing import",
                affected_files=["src/main.py"],
                confirmed=True,
            ),
            timestamp="2024-01-01T00:00:00",
        )
        md = report.to_markdown()
        assert "# Diagnosis Report" in md
        assert "l4-diagnoser" in md
        assert "Missing import" in md
        assert "src/main.py" in md
        assert "Confirmed" in md

    def test_report_save_creates_file(self):
        """Scenario: Report written to change directory."""
        report = DiagnosisReport(
            change_name="l4-diagnoser",
            hypotheses=[],
            confirmed_hypothesis=None,
            fix_plan=FixPlan(
                root_cause="Test",
                fix_description="Test fix",
                affected_files=[],
                confirmed=False,
            ),
            timestamp="2024-01-01T00:00:00",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            transport = LocalTransport()
            report.save(tmpdir, transport)
            assert os.path.exists(f"{tmpdir}/diagnosis.md")
            with open(f"{tmpdir}/diagnosis.md") as f:
                content = f.read()
            assert "Diagnosis Report" in content


# ---------------------------------------------------------------------------
# Full diagnosis cycle
# ---------------------------------------------------------------------------

class TestFullDiagnoseCycle:
    """Test the complete diagnose() method."""

    def test_full_cycle_returns_report(self):
        d = Diagnoser()
        with tempfile.TemporaryDirectory() as tmpdir:
            transport = LocalTransport()
            failure_info = {
                "detail": "ImportError: No module named 'nonexistent_module'",
                "verify_feedback": "Verifier found issues",
                "change_name": "test-change",
            }
            report = d.diagnose(failure_info, tmpdir, transport)
            assert isinstance(report, DiagnosisReport)
            assert report.change_name == "test-change"
            assert len(report.hypotheses) >= 1
            assert isinstance(report.fix_plan, FixPlan)
            assert isinstance(report.timestamp, str)


# ---------------------------------------------------------------------------
# Task 1.3: Enhanced root-cause classification tests
# ---------------------------------------------------------------------------

class TestImportErrorRootCause:
    """ImportError produces specific root cause even without probe confirmation."""

    def test_import_error_no_generic_unconfirmed(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(
                rank=1,
                description="Missing or incorrect import / dependency",
                confidence=0.9,
                evidence="ImportError: No module named 'some_module'",
                probe_result=ProbeResult(confirmed=False, evidence="not found", probe_type="search"),
            ),
        ]
        plan = d.targeted_fix(hyps)
        assert plan.confirmed is False
        assert "unconfirmed hypothesis" not in plan.fix_description.lower()
        assert "some_module" in plan.fix_description

    def test_import_error_mentions_module_name(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(
                rank=1,
                description="Missing or incorrect import / dependency",
                confidence=0.9,
                evidence="ModuleNotFoundError: No module named 'xyz'",
                probe_result=ProbeResult(confirmed=False, evidence="no", probe_type="search"),
            ),
        ]
        plan = d.targeted_fix(hyps)
        assert "xyz" in plan.fix_description


class TestLintErrorRootCause:
    """Lint error produces specific root cause even without probe confirmation."""

    def test_lint_error_specific_fix(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(
                rank=1,
                description="Code style or syntax violation",
                confidence=0.75,
                evidence="E701 Multiple statements on one line (colon)\n   --> src/foo.py:42:35",
                probe_result=ProbeResult(confirmed=False, evidence="none", probe_type="diagnostics"),
            ),
        ]
        plan = d.targeted_fix(hyps)
        assert plan.confirmed is False
        assert "E701" in plan.fix_description
        assert "src/foo.py" in plan.fix_description
        assert "unconfirmed hypothesis" not in plan.fix_description.lower()

    def test_lint_error_affected_files(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(
                rank=1,
                description="Code style or syntax violation",
                confidence=0.75,
                evidence="E701 Multiple statements on one line (colon)\n   --> src/foo.py:42:35",
                probe_result=ProbeResult(confirmed=False, evidence="none", probe_type="diagnostics"),
            ),
        ]
        plan = d.targeted_fix(hyps)
        assert "src/foo.py" in plan.affected_files


class TestAssertionErrorRootCause:
    """AssertionError produces specific root cause."""

    def test_assertion_error_specific_root_cause(self):
        d = Diagnoser()
        hyps = [
            Hypothesis(
                rank=1,
                description="Test expectation mismatch",
                confidence=0.8,
                evidence="FAILED test_foo.py::test_bar - AssertionError: expected 42",
                probe_result=ProbeResult(confirmed=False, evidence="no", probe_type="search"),
            ),
        ]
        plan = d.targeted_fix(hyps)
        assert "assertion" in plan.root_cause.lower() or "expectation" in plan.root_cause.lower()
        assert "unconfirmed hypothesis" not in plan.fix_description.lower()
        # Should reference test name
        assert "test_bar" in plan.fix_description or "test_foo" in plan.fix_description


class TestGenericErrorHasContext:
    """Unknown error pattern still produces actionable hypothesis."""

    def test_unknown_error_includes_evidence_snippet(self):
        d = Diagnoser()
        failure = {
            "detail": "some bizarre custom error that matches nothing xyz ABC123DEF",
        }
        hyps = d.hypothesize(failure)
        # At least one hypothesis should reference actual error detail
        evidence_texts = " ".join(h.evidence for h in hyps)
        assert "bizarre" in evidence_texts or "ABC123DEF" in evidence_texts or "xyz" in evidence_texts

    def test_multiple_patterns_no_generic_displacement(self):
        """Generic fallbacks should not displace specific matched hypotheses."""
        d = Diagnoser()
        failure = {
            "detail": "ImportError: No module named 'foo'\nTypeError: unsupported operand",
        }
        hyps = d.hypothesize(failure)
        descriptions = [h.description.lower() for h in hyps]
        # Should have specific import AND type error hypotheses
        has_import = any("import" in d or "module" in d or "dependency" in d for d in descriptions)
        has_type = any("type" in d for d in descriptions)
        assert has_import
        assert has_type


# ---------------------------------------------------------------------------
# Task 2.3: Verify pre-check tests
# ---------------------------------------------------------------------------

class TestVerifyPrecheck:
    """Tests for the verify_precheck function."""

    def test_precheck_detects_import_error(self):
        """Pre-check detects import error in changed file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with a broken import
            bad_file = os.path.join(tmpdir, "broken.py")
            with open(bad_file, "w") as f:
                f.write("import nonexistent_xyz_module\n")
            transport = LocalTransport()
            result = verify_precheck(tmpdir, ["broken.py"], transport)
            assert isinstance(result, PreCheckResult)
            assert result.passed is False
            assert result.error_type == "import_error"
            assert "broken.py" in result.file_path

    def test_precheck_detects_lint_error(self):
        """Pre-check detects lint error in changed file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with E701 violation
            bad_file = os.path.join(tmpdir, "linty.py")
            with open(bad_file, "w") as f:
                f.write("if True: pass\n")
            transport = LocalTransport()
            result = verify_precheck(tmpdir, ["linty.py"], transport)
            assert isinstance(result, PreCheckResult)
            assert result.passed is False
            assert result.error_type == "lint_error"
            assert "linty.py" in result.file_path

    def test_precheck_passes_on_clean_file(self):
        """Pre-check passes on clean file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            clean_file = os.path.join(tmpdir, "clean.py")
            with open(clean_file, "w") as f:
                f.write("x = 1\ny = 2\nprint(x + y)\n")
            transport = LocalTransport()
            result = verify_precheck(tmpdir, ["clean.py"], transport)
            assert isinstance(result, PreCheckResult)
            assert result.passed is True
            assert result.error_type == ""
            assert result.file_path == ""

    def test_precheck_no_py_files_passes(self):
        """Pre-check passes when no Python files are in changed set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transport = LocalTransport()
            result = verify_precheck(tmpdir, ["readme.md", "data.json"], transport)
            assert result.passed is True

    def test_precheck_result_has_required_fields(self):
        """PreCheckResult has all required fields."""
        result = PreCheckResult(passed=True, error_type="", file_path="", message="")
        assert isinstance(result.passed, bool)
        assert isinstance(result.error_type, str)
        assert isinstance(result.file_path, str)
        assert isinstance(result.message, str)
