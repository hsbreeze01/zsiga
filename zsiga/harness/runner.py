"""Harness runner — discovers and runs tests, collecting structured events."""

from __future__ import annotations

import importlib.util
import time
import traceback
from dataclasses import dataclass, field
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
