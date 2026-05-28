"""Tests for zsiga.harness.runner — HarnessRunner, events, and HarnessResult."""

from __future__ import annotations

import textwrap
from pathlib import Path

from zsiga.harness.runner import (
    HarnessResult,
    HarnessRunner,
    QualificationReport,
    TestError,
    TestEvent,
    TestFailed,
    TestPassed,
    TestReport,
    TestStarted,
)


# ---------------------------------------------------------------------------
# Event dataclass tests
# ---------------------------------------------------------------------------


class TestEventDataclasses:
    """Verify event dataclass structure."""

    def test_test_started(self) -> None:
        evt = TestStarted(test_name="foo", timestamp=1.0)
        assert evt.test_name == "foo"
        assert isinstance(evt, TestEvent)

    def test_test_passed(self) -> None:
        evt = TestPassed(test_name="foo", timestamp=1.0, duration_ms=42.0)
        assert evt.duration_ms == 42.0

    def test_test_failed(self) -> None:
        evt = TestFailed(
            test_name="foo", timestamp=1.0, duration_ms=10.0, error_message="boom",
        )
        assert evt.error_message == "boom"

    def test_test_error(self) -> None:
        evt = TestError(test_name="foo", timestamp=1.0, error_message="err")
        assert evt.error_message == "err"


# ---------------------------------------------------------------------------
# HarnessResult tests
# ---------------------------------------------------------------------------


class TestHarnessResult:
    """Verify HarnessResult aggregation."""

    def test_default_counts(self) -> None:
        result = HarnessResult()
        assert result.total == 0
        assert result.passed == 0
        assert result.failed == 0
        assert result.errors == 0
        assert result.events == []

    def test_custom_counts(self) -> None:
        result = HarnessResult(total=5, passed=3, failed=1, errors=1)
        assert result.total == 5


# ---------------------------------------------------------------------------
# HarnessRunner.discover() tests
# ---------------------------------------------------------------------------


class TestHarnessRunnerDiscover:
    """Verify test discovery."""

    def test_discovers_test_files(self, tmp_path: Path) -> None:
        (tmp_path / "test_alpha.py").write_text("# test")
        (tmp_path / "test_beta.py").write_text("# test")
        (tmp_path / "helper.py").write_text("# not a test")

        runner = HarnessRunner()
        found = runner.discover(tmp_path)

        names = [p.name for p in found]
        assert "test_alpha.py" in names
        assert "test_beta.py" in names
        assert "helper.py" not in names

    def test_discover_empty_dir(self, tmp_path: Path) -> None:
        runner = HarnessRunner()
        found = runner.discover(tmp_path)
        assert found == []

    def test_discover_nonexistent_dir(self) -> None:
        runner = HarnessRunner()
        try:
            runner.discover("/nonexistent/path/xyz")
            assert False, "Should have raised"
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# HarnessRunner.run() tests
# ---------------------------------------------------------------------------


class TestHarnessRunnerRun:
    """Verify test execution and event emission."""

    def test_run_passing_tests(self, tmp_path: Path) -> None:
        (tmp_path / "test_sample.py").write_text(
            textwrap.dedent("""\
                def test_ok():
                    assert True
            """),
        )

        runner = HarnessRunner()
        runner.discover(tmp_path)
        result = runner.run()

        assert result.total == 1
        assert result.passed == 1
        assert result.failed == 0

        # Check events
        started = [e for e in result.events if isinstance(e, TestStarted)]
        passed = [e for e in result.events if isinstance(e, TestPassed)]
        assert len(started) == 1
        assert len(passed) == 1

    def test_run_failing_tests(self, tmp_path: Path) -> None:
        (tmp_path / "test_fail.py").write_text(
            textwrap.dedent("""\
                def test_bad():
                    assert False
            """),
        )

        runner = HarnessRunner()
        runner.discover(tmp_path)
        result = runner.run()

        assert result.failed == 1
        assert result.passed == 0

        failed_events = [e for e in result.events if isinstance(e, TestFailed)]
        assert len(failed_events) == 1
        assert failed_events[0].error_message != ""

    def test_run_error_tests(self, tmp_path: Path) -> None:
        (tmp_path / "test_err.py").write_text(
            textwrap.dedent("""\
                def test_boom():
                    raise RuntimeError("unexpected")
            """),
        )

        runner = HarnessRunner()
        runner.discover(tmp_path)
        result = runner.run()

        assert result.errors == 1

        error_events = [e for e in result.events if isinstance(e, TestError)]
        assert len(error_events) == 1

    def test_run_multiple_files(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text(
            textwrap.dedent("""\
                def test_one():
                    assert 1 == 1
            """),
        )
        (tmp_path / "test_b.py").write_text(
            textwrap.dedent("""\
                def test_two():
                    assert False
            """),
        )

        runner = HarnessRunner()
        runner.discover(tmp_path)
        result = runner.run()

        assert result.total == 2
        assert result.passed == 1
        assert result.failed == 1

    def test_results_property(self, tmp_path: Path) -> None:
        (tmp_path / "test_x.py").write_text(
            textwrap.dedent("""\
                def test_ok():
                    pass
            """),
        )

        runner = HarnessRunner()
        runner.discover(tmp_path)
        runner.run()

        assert runner.results.total == 1
        assert runner.results.passed == 1

    def test_run_no_discovery(self) -> None:
        """Running without discover should return empty result."""
        runner = HarnessRunner()
        result = runner.run()
        assert result.total == 0
        assert result.passed == 0

    def test_event_timestamps_populated(self, tmp_path: Path) -> None:
        (tmp_path / "test_ts.py").write_text(
            textwrap.dedent("""\
                def test_ok():
                    pass
            """),
        )

        runner = HarnessRunner()
        runner.discover(tmp_path)
        result = runner.run()

        for event in result.events:
            assert event.timestamp > 0


# ---------------------------------------------------------------------------
# HarnessRunner.run_pytest fail-closed tests
# ---------------------------------------------------------------------------


class TestHarnessRunnerPytestFailClosed:
    def test_run_pytest_empty_file_returns_harness_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("# no tests here\n")
        output_path = tmp_path / "results.jsonl"

        reports = HarnessRunner().run_pytest([str(test_file)], str(output_path))

        assert reports
        assert reports[-1].status == "error"
        assert "no executable test results" in reports[-1].message
        assert output_path.exists()

    def test_run_pytest_collection_error_returns_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_bad_syntax.py"
        test_file.write_text("def test_bad(:\n")

        reports = HarnessRunner().run_pytest([str(test_file)], str(tmp_path / "out.jsonl"))

        assert any(r.status == "error" for r in reports)
        assert any("SyntaxError" in r.message or "ERROR" in r.message for r in reports)

    def test_qualification_report_empty_results_can_be_failed(self) -> None:
        report = QualificationReport(
            capability_results=[],
            regression_results=[],
            passed=False,
        )

        assert report.passed is False

    def test_test_report_dataclass_fields(self) -> None:
        report = TestReport(
            name="tests/test_sample.py::test_ok",
            status="passed",
            duration_s=0.1,
            message="",
        )

        assert report.name.endswith("test_ok")
        assert report.status == "passed"
