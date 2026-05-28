"""Harness runner — discovers and runs tests, collecting structured events."""

from __future__ import annotations

import importlib.util
import json
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Event dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TestEvent:
    """Base class for test lifecycle events."""

    __test__ = False  # prevent pytest collection

    test_name: str
    timestamp: float


@dataclass
class TestStarted(TestEvent):
    """Emitted when a test begins execution."""


@dataclass
class TestPassed(TestEvent):
    """Emitted when a test passes."""

    duration_ms: float = 0.0


@dataclass
class TestFailed(TestEvent):
    """Emitted when a test fails (assertion error)."""

    duration_ms: float = 0.0
    error_message: str = ""


@dataclass
class TestError(TestEvent):
    """Emitted when a test raises an unexpected error."""

    error_message: str = ""


# ---------------------------------------------------------------------------
# HarnessResult
# ---------------------------------------------------------------------------


@dataclass
class HarnessResult:
    """Aggregated result summary from a harness run."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    events: list[TestEvent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Structured report dataclasses (spec-driven)
# ---------------------------------------------------------------------------


@dataclass
class TestReport:
    """Structured report for a single test result."""

    __test__ = False  # prevent pytest collection

    name: str
    status: str  # "passed" | "failed" | "error"
    duration_s: float
    message: str


@dataclass
class QualificationReport:
    """Combined report from capability + regression test suites."""

    __test__ = False

    capability_results: list[TestReport]
    regression_results: list[TestReport]
    passed: bool  # True only if ALL results have status "passed"


# ---------------------------------------------------------------------------
# HarnessRunner
# ---------------------------------------------------------------------------


class HarnessRunner:
    """Discovers test files within a directory, executes them, and collects
    structured results.

    Usage::

        runner = HarnessRunner()
        tests = runner.discover("./tests")
        runner.run()
        print(runner.results)
    """

    def __init__(self, fixtures: list[Any] | None = None) -> None:
        self._test_files: list[Path] = []
        self._fixtures: list[Any] = fixtures or []
        self._result = HarnessResult()

    # -- discovery -----------------------------------------------------------

    def discover(self, directory: str | Path) -> list[Path]:
        """Find test files matching ``test_*.py`` under *directory*.

        Returns the list of discovered paths (also stored internally).
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        self._test_files = sorted(dir_path.glob("test_*.py"))
        return list(self._test_files)

    # -- execution -----------------------------------------------------------

    def run(self) -> HarnessResult:
        """Execute every discovered test and collect structured events.

        Each test function whose name starts with ``test_`` inside the
        discovered modules is invoked in an isolated context.
        """
        self._result = HarnessResult(total=len(self._test_files))
        for test_file in self._test_files:
            self._run_file(test_file)
        return self._result

    # -- results -------------------------------------------------------------

    @property
    def results(self) -> HarnessResult:
        """Return the most recent :class:`HarnessResult`."""
        return self._result

    # -- internals -----------------------------------------------------------

    def _run_file(self, test_file: Path) -> None:
        """Load a single test module and run every ``test_*`` function."""
        module_name = test_file.stem
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        if spec is None or spec.loader is None:
            event = TestError(
                test_name=module_name,
                timestamp=time.time(),
                error_message=f"Could not load module from {test_file}",
            )
            self._result.events.append(event)
            self._result.errors += 1
            return

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            event = TestError(
                test_name=module_name,
                timestamp=time.time(),
                error_message=traceback.format_exc(),
            )
            self._result.events.append(event)
            self._result.errors += 1
            return

        # Find test functions
        test_fns = sorted(
            [
                name
                for name in dir(module)
                if name.startswith("test_") and callable(getattr(module, name))
            ],
        )

        for fn_name in test_fns:
            full_name = f"{module_name}::{fn_name}"
            start = time.time()
            self._result.events.append(
                TestStarted(test_name=full_name, timestamp=start),
            )
            try:
                getattr(module, fn_name)()
                elapsed_ms = (time.time() - start) * 1000
                self._result.events.append(
                    TestPassed(
                        test_name=full_name,
                        timestamp=time.time(),
                        duration_ms=elapsed_ms,
                    ),
                )
                self._result.passed += 1
            except AssertionError:
                elapsed_ms = (time.time() - start) * 1000
                self._result.events.append(
                    TestFailed(
                        test_name=full_name,
                        timestamp=time.time(),
                        duration_ms=elapsed_ms,
                        error_message=traceback.format_exc(),
                    ),
                )
                self._result.failed += 1
            except Exception:
                self._result.events.append(
                    TestError(
                        test_name=full_name,
                        timestamp=time.time(),
                        error_message=traceback.format_exc(),
                    ),
                )
                self._result.errors += 1

    # -- pytest-based execution (spec-driven) --------------------------------

    def run_pytest(
        self,
        test_paths: list[str],
        output_path: str = "harness-results.jsonl",
    ) -> list[TestReport]:
        """Execute tests via ``pytest.main()`` and return :class:`TestReport` list.

        Args:
            test_paths: Paths passed to pytest (files or directories).
            output_path: File path for JSONL event output.

        Returns:
            A list of :class:`TestReport` instances, one per test item.
        """
        plugin = _HarnessCollectorPlugin(output_path=output_path)
        args = list(test_paths) + ["-p", "no:cacheprovider", "--tb=short"]

        import pytest

        exit_code = pytest.main(args, plugins=[plugin])
        try:
            exit_value = int(exit_code)
        except (TypeError, ValueError):
            exit_value = 1

        if not plugin.reports:
            plugin.add_harness_error(
                "pytest collected no executable test results",
            )
        elif exit_value != 0 and all(r.status == "passed" for r in plugin.reports):
            plugin.add_harness_error(
                f"pytest exited with non-zero status {exit_value}",
            )

        return plugin.reports


# ---------------------------------------------------------------------------
# Internal pytest plugin for collecting TestReport objects
# ---------------------------------------------------------------------------


class _HarnessCollectorPlugin:
    """A pytest plugin that collects ``TestReport`` objects and emits JSONL."""

    def __init__(self, output_path: str = "harness-results.jsonl") -> None:
        self.output_path = output_path
        self.reports: list[TestReport] = []
        self._start_times: dict[str, float] = {}

    def add_harness_error(self, message: str) -> None:
        report = TestReport(
            name="__harness__::pytest",
            status="error",
            duration_s=0.0,
            message=message,
        )
        self.reports.append(report)
        self._append_jsonl(report)

    def pytest_collection_modifyitems(self, session: Any, items: Any) -> None:
        # Record no-op; collection is handled by pytest
        pass

    def pytest_collectreport(self, report: Any) -> None:
        if getattr(report, "failed", False):
            test_report = TestReport(
                name=getattr(report, "nodeid", "__collection__"),
                status="error",
                duration_s=0.0,
                message=str(report.longrepr) if getattr(report, "longrepr", None) else "collection failed",
            )
            self.reports.append(test_report)
            self._append_jsonl(test_report)

    def pytest_runtest_logstart(self, nodeid: str, location: Any) -> None:
        self._start_times[nodeid] = time.time()

    def pytest_runtest_logreport(self, report: Any) -> None:
        # We only care about the "call" phase for test results
        if report.when != "call":
            return

        duration_s = getattr(report, "duration", 0.0)
        message = ""

        if report.passed:
            status = "passed"
        elif report.failed:
            status = "failed"
            message = str(report.longrepr) if report.longrepr else ""
        else:
            status = "error"
            message = str(report.longrepr) if report.longrepr else ""

        test_report = TestReport(
            name=report.nodeid,
            status=status,
            duration_s=round(duration_s, 6),
            message=message,
        )
        self.reports.append(test_report)
        self._append_jsonl(test_report)

    def _append_jsonl(self, report: TestReport) -> None:
        """Append one JSON line to the JSONL output file."""
        line = json.dumps(
            {
                "name": report.name,
                "status": report.status,
                "duration_s": report.duration_s,
                "message": report.message,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as fh:
            fh.write(line + "\n")
