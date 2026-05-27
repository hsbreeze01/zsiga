"""Tests for verify failure classification, observability, and verify rate report."""

from zsiga.pipeline.verifier import classify_verify_failure
from zsiga.metrics.types import PhaseRecord, Phase, Outcome, ChangeRecord
from zsiga.metrics.collector import compute_stats
from zsiga.metrics.verify_rate import compute_verify_rate_report


# ---------------------------------------------------------------------------
# Spec: verify-failure-classification.md
# ---------------------------------------------------------------------------

class TestClassifyVerifyFailure:
    """Tests for classify_verify_failure function."""

    def test_classify_lint_failure(self):
        """Scenario: Classify lint failure."""
        verify_md = (
            "Verdict: FAIL\n\n"
            "E701 Multiple statements on one line (colon)\n"
            "ruff check output shows errors\n"
        )
        mech_results = {
            "lint": {"passed": False, "output": "E701 ..."},
            "test": {"passed": True, "output": ""},
        }
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results=mech_results,
        )
        assert result == "lint"

    def test_classify_test_failure(self):
        """Scenario: Classify test failure."""
        verify_md = "FAILED test_foo.py::test_bar - assertion error"
        mech_results = {
            "lint": {"passed": True, "output": ""},
            "test": {"passed": False, "output": "FAILED test_foo.py::test_bar"},
        }
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results=mech_results,
        )
        assert result == "test"

    def test_classify_layer1_pytest_failure(self):
        """Scenario: Classify layer1_pytest failure."""
        layer1_result = {"passed": False, "vacuous": False}
        result = classify_verify_failure(
            verify_md="Verdict: FAIL",
            mech_results={
                "lint": {"passed": True, "output": ""},
                "test": {"passed": True, "output": ""},
            },
            layer1_result=layer1_result,
        )
        assert result == "layer1_pytest"

    def test_classify_unknown_when_no_verify_md(self):
        """Scenario: Classify unknown when no verify.md."""
        result = classify_verify_failure(
            verify_md="",
            mech_results=None,
        )
        assert result == "unknown"

    def test_classify_llm_judge(self):
        """Scenario: Classify llm_judge when content exists but no specific match."""
        verify_md = (
            "Verdict: FAIL\n\n"
            "The implementation does not match the spec requirements."
        )
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results={
                "lint": {"passed": True, "output": ""},
                "test": {"passed": True, "output": ""},
            },
        )
        assert result == "llm_judge"


# ---------------------------------------------------------------------------
# Spec: verify-failure-classification.md — PhaseRecord persistence
# ---------------------------------------------------------------------------

class TestPhaseRecordFailureCategory:
    """Tests for failure_category in PhaseRecord."""

    def test_failure_category_in_to_dict(self):
        """Scenario: Failure category recorded in PhaseRecord."""
        rec = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            failure_category="lint",
        )
        d = rec  # PhaseRecord is a dataclass
        assert d.failure_category == "lint"

    def test_failure_category_in_change_record_to_dict(self):
        """Verify that to_dict() includes failure_category."""
        pr = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.FAIL,
            failure_category="test",
            detail="some detail",
        )
        cr = ChangeRecord(
            change_name="test-change",
            project="zsiga",
            outcome=Outcome.REVERTED,
            phases=[pr],
        )
        result = cr.to_dict()
        assert result["phases"][0]["failure_category"] == "test"

    def test_default_failure_category_is_empty(self):
        """Verify default failure_category is empty string."""
        pr = PhaseRecord(
            phase=Phase.VERIFY,
            outcome=Outcome.SUCCESS,
        )
        assert pr.failure_category == ""


# ---------------------------------------------------------------------------
# Spec: verify-failure-classification.md — compute_stats breakdown
# ---------------------------------------------------------------------------

class TestComputeStatsVerifyBreakdown:
    """Tests for verify_failure_breakdown in compute_stats."""

    def _make_change(self, name, verify_outcome, failure_category=""):
        phases = [
            {
                "phase": "verify",
                "outcome": verify_outcome,
                "failure_category": failure_category,
                "turns_used": 0,
                "seconds_used": 0.0,
                "fix_attempts": 0,
                "llm_calls": 0,
                "tool_calls": 0,
                "detail": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "compaction_count": 0,
                "sub_agent_count": 0,
                "model": "glm-5.1",
                "provider": "zhipuai",
            }
        ]
        return {
            "change_name": name,
            "project": "zsiga",
            "outcome": "success" if verify_outcome == "success" else "fail",
            "phases": phases,
        }

    def test_verify_failure_breakdown(self):
        """Scenario: Verify failure breakdown in stats output."""
        changes = [
            self._make_change("c1", "fail", "lint"),
            self._make_change("c2", "fail", "test"),
            self._make_change("c3", "fail", "lint"),
        ]
        stats = compute_stats(changes)
        assert "verify_failure_breakdown" in stats
        assert stats["verify_failure_breakdown"]["lint"] == 2
        assert stats["verify_failure_breakdown"]["test"] == 1

    def test_empty_changes_breakdown(self):
        """Empty changes produce empty breakdown."""
        stats = compute_stats([])
        assert stats["verify_failure_breakdown"] == {}


# ---------------------------------------------------------------------------
# Spec: verify-rate-metric-script.md
# ---------------------------------------------------------------------------

class TestComputeVerifyRateReport:
    """Tests for compute_verify_rate_report."""

    def _make_change(
        self, name, project, verify_outcome, failure_category=""
    ):
        phases = [
            {
                "phase": "verify",
                "outcome": verify_outcome,
                "failure_category": failure_category,
                "turns_used": 0,
                "seconds_used": 0.0,
                "fix_attempts": 0,
                "llm_calls": 0,
                "tool_calls": 0,
                "detail": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "compaction_count": 0,
                "sub_agent_count": 0,
                "model": "glm-5.1",
                "provider": "zhipuai",
            }
        ]
        return {
            "change_name": name,
            "project": project,
            "outcome": "success" if verify_outcome == "success" else "fail",
            "started_at": "2026-05-21T00:00:00",
            "finished_at": "2026-05-21T01:00:00",
            "phases": phases,
        }

    def test_report_overall_rate(self):
        """Scenario: Report contains overall verify pass rate."""
        changes = []
        for i in range(63):
            changes.append(
                self._make_change(f"c{i}", "zsiga", "success")
            )
        for i in range(65):
            changes.append(
                self._make_change(f"f{i}", "zsiga", "fail", "unknown")
            )
        report = compute_verify_rate_report(changes)
        assert report["verify_pass_rate_pct"] == 49.2

    def test_report_per_project_breakdown(self):
        """Scenario: Report contains per-project breakdown."""
        changes = []
        # zsiga: 26 pass out of 70
        for i in range(26):
            changes.append(
                self._make_change(f"zs{i}", "zsiga", "success")
            )
        for i in range(44):
            changes.append(
                self._make_change(f"zf{i}", "zsiga", "fail", "unknown")
            )
        # compass: 20 pass out of 28
        for i in range(20):
            changes.append(
                self._make_change(f"cs{i}", "compass", "success")
            )
        for i in range(8):
            changes.append(
                self._make_change(f"cf{i}", "compass", "fail", "unknown")
            )
        report = compute_verify_rate_report(changes)
        assert abs(report["by_project"]["zsiga"] - 37.1) < 0.2
        assert abs(report["by_project"]["compass"] - 71.4) < 0.2

    def test_report_failure_breakdown_by_category(self):
        """Scenario: Report contains failure breakdown by category."""
        changes = []
        for i in range(20):
            changes.append(
                self._make_change(f"u{i}", "zsiga", "fail", "unknown")
            )
        for i in range(10):
            changes.append(
                self._make_change(f"l{i}", "zsiga", "fail", "llm_judge")
            )
        for i in range(8):
            changes.append(
                self._make_change(f"li{i}", "zsiga", "fail", "lint")
            )
        report = compute_verify_rate_report(changes)
        assert report["failure_breakdown"]["unknown"] == 20
        assert report["failure_breakdown"]["llm_judge"] == 10
        assert report["failure_breakdown"]["lint"] == 8

    def test_report_empty_changes(self):
        """Scenario: Report handles empty change list gracefully."""
        report = compute_verify_rate_report([])
        assert report["verify_pass_rate_pct"] == 0.0
        assert report["by_project"] == {}
        assert report["failure_breakdown"] == {}
        assert report["rolling_window"] == []

    def test_report_has_rolling_window(self):
        """Report produces rolling window entries."""
        changes = []
        for i in range(25):
            changes.append(
                self._make_change(f"c{i}", "zsiga", "success")
            )
        report = compute_verify_rate_report(changes)
        assert len(report["rolling_window"]) == 25
        # Last entry should be 100% since all pass
        assert report["rolling_window"][-1]["rate"] == 100.0

    def test_report_has_top_failure_patterns(self):
        """Report produces top failure patterns."""
        changes = []
        for i in range(5):
            changes.append(
                self._make_change(f"c{i}", "zsiga", "fail", "lint")
            )
        for i in range(3):
            changes.append(
                self._make_change(f"d{i}", "zsiga", "fail", "test")
            )
        report = compute_verify_rate_report(changes)
        assert len(report["top_failure_patterns"]) == 2
        assert report["top_failure_patterns"][0]["category"] == "lint"
        assert report["top_failure_patterns"][0]["count"] == 5
        assert report["top_failure_patterns"][1]["category"] == "test"
        assert report["top_failure_patterns"][1]["count"] == 3


# ---------------------------------------------------------------------------
# Spec: verify-failure-observability.md — _build_verify_detail helper
# ---------------------------------------------------------------------------

class TestBuildVerifyDetail:
    """Tests for the _build_verify_detail helper."""

    def test_build_detail_with_verdict_and_content(self):
        from zsiga.pipeline.orchestrator import _build_verify_detail
        detail = _build_verify_detail(
            "FAIL",
            "Layer 1: FAIL — 2 testable scenarios",
        )
        assert "FAIL" in detail
        assert "Layer 1" in detail

    def test_build_detail_includes_extra(self):
        from zsiga.pipeline.orchestrator import _build_verify_detail
        detail = _build_verify_detail(
            "FAIL",
            "some content",
            "eval-fix attempts=3",
        )
        assert "eval-fix attempts=3" in detail

    def test_build_detail_empty(self):
        from zsiga.pipeline.orchestrator import _build_verify_detail
        detail = _build_verify_detail("", "", "")
        assert detail == ""


# ---------------------------------------------------------------------------
# Spec: verify-failure-observability.md — _classify_and_build_verify_record
# ---------------------------------------------------------------------------

class TestClassifyAndBuildVerifyRecord:
    """Tests for the _classify_and_build_verify_record helper."""

    def test_fail_record_has_category_and_detail(self):
        from zsiga.pipeline.orchestrator import _classify_and_build_verify_record
        verify_md = (
            "Verdict: FAIL\nLayer 1: FAIL — 2 testable scenarios"
            " more content here that is at least fifty characters long"
        )
        rec = _classify_and_build_verify_record(
            outcome=Outcome.FAIL,
            seconds=5.0,
            fix_attempts=2,
            verify_md_content=verify_md,
            mech_results={
                "lint": {"passed": False, "output": "E701"},
                "test": {"passed": True, "output": ""},
            },
        )
        assert rec.phase == Phase.VERIFY
        assert rec.outcome == Outcome.FAIL
        assert rec.failure_category == "lint"
        assert "FAIL" in rec.detail
        assert len(rec.detail) > 50

    def test_success_record_has_no_category(self):
        from zsiga.pipeline.orchestrator import _classify_and_build_verify_record
        rec = _classify_and_build_verify_record(
            outcome=Outcome.SUCCESS,
            seconds=3.0,
            fix_attempts=0,
            verify_md_content="Verdict: PASS\nLayer 1: PASS — 3 testable scenarios",
        )
        assert rec.failure_category == ""
        assert "PASS" in rec.detail

    def test_revert_record_has_eval_fix_detail(self):
        from zsiga.pipeline.orchestrator import _classify_and_build_verify_record
        rec = _classify_and_build_verify_record(
            outcome=Outcome.FAIL,
            seconds=10.0,
            fix_attempts=3,
            verify_md_content="Verdict: FAIL",
            extra_detail="eval-fix attempts=3",
        )
        assert "eval-fix" in rec.detail
        assert "3" in rec.detail

    def test_precheck_failure_record(self):
        from zsiga.pipeline.orchestrator import _classify_and_build_verify_record
        verify_md = (
            "Verdict: FAIL\n\nPre-check failure (import):\n"
            "cannot import module in zsiga/foo.py"
        )
        rec = _classify_and_build_verify_record(
            outcome=Outcome.FAIL,
            seconds=0.0,
            fix_attempts=0,
            verify_md_content=verify_md,
            extra_detail="eval-fix attempts=0; pre-check: import in zsiga/foo.py",
        )
        assert "import" in rec.detail
        assert "zsiga/foo.py" in rec.detail


# ---------------------------------------------------------------------------
# Layer 0 check failure classification
# ---------------------------------------------------------------------------

class TestLayer0CheckClassification:
    """Tests for layer0_check failure category in classify_verify_failure."""

    def test_classify_layer0_check_from_verify_md(self):
        """Scenario: Classify layer0_check from verify.md pattern."""
        verify_md = "Verdict: FAIL\nverify L0 FAIL: 7/8 checks passed (spec_scenario_coverage)"
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results={"lint": {"passed": True, "output": ""},
                          "test": {"passed": True, "output": ""}},
        )
        assert result == "layer0_check:spec_scenario_coverage"

    def test_classify_layer0_check_from_l0_fail_pattern(self):
        """Scenario: Classify layer0_check from L0 FAIL pattern."""
        verify_md = "Verdict: FAIL\nL0 FAIL: missing spec coverage (spec_file_coverage)"
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results={"lint": {"passed": True, "output": ""},
                          "test": {"passed": True, "output": ""}},
        )
        assert result == "layer0_check:spec_file_coverage"

    def test_classify_layer0_check_with_result_param(self):
        """Scenario: Precise classification using layer0_result parameter."""
        layer0_result = {
            "passed": False,
            "failed_checks": ["tasks_completion", "spec_file_coverage"],
        }
        result = classify_verify_failure(
            verify_md="Verdict: FAIL",
            mech_results={"lint": {"passed": True, "output": ""},
                          "test": {"passed": True, "output": ""}},
            layer0_result=layer0_result,
        )
        assert result == "layer0_check:tasks_completion"

    def test_classify_layer0_check_with_single_failed_check(self):
        """Scenario: Single failed L0 check in result param."""
        layer0_result = {
            "passed": False,
            "failed_checks": ["spec_scenario_coverage"],
        }
        result = classify_verify_failure(
            verify_md="Verdict: FAIL",
            mech_results={"lint": {"passed": True, "output": ""},
                          "test": {"passed": True, "output": ""}},
            layer0_result=layer0_result,
        )
        assert result == "layer0_check:spec_scenario_coverage"

    def test_layer0_result_takes_priority_over_heuristic(self):
        """Scenario: layer0_result param takes priority over verify.md heuristic."""
        layer0_result = {
            "passed": False,
            "failed_checks": ["bac_acceptance"],
        }
        verify_md = "Verdict: FAIL\nchecks passed (spec_scenario_coverage)"
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results={"lint": {"passed": True, "output": ""},
                          "test": {"passed": True, "output": ""}},
            layer0_result=layer0_result,
        )
        assert result == "layer0_check:bac_acceptance"

    def test_layer0_not_triggered_when_passed(self):
        """Scenario: No layer0_check when result shows passed."""
        layer0_result = {
            "passed": True,
            "failed_checks": [],
        }
        verify_md = "Verdict: FAIL\nSome other reason"
        result = classify_verify_failure(
            verify_md=verify_md,
            mech_results={"lint": {"passed": True, "output": ""},
                          "test": {"passed": True, "output": ""}},
            layer0_result=layer0_result,
        )
        assert result == "llm_judge"
