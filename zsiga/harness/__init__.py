"""zsiga harness package — re-exports public API for test harness."""

from pathlib import Path

from zsiga.harness.conftest import (
    MockLLMClient,
    MockTransport,
    TempGitRepo,
    mock_llm_client,
    mock_transport,
    temp_git_repo,
)
from zsiga.harness.phase_contract import (
    ContractViolation,
    PhaseContractError,
    PhaseContractHarness,
    PhaseContractResult,
)
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


def run_capability_tests(
    output_path: str = "harness-results.jsonl",
) -> list[TestReport]:
    """Execute the L4 capability test suite and return structured results.

    Returns:
        A list of :class:`TestReport` instances, one per test item.
    """
    runner = HarnessRunner()
    return runner.run_pytest(
        [
            str(Path("zsiga/harness/capability")),
        ],
        output_path=output_path,
    )


def run_behavioral_tests(
    output_path: str = "harness-results.jsonl",
) -> list[TestReport]:
    """Execute the behavioral (adversarial + boundary) test suite.

    Returns:
        A list of :class:`TestReport` instances, one per test item.
    """
    runner = HarnessRunner()
    return runner.run_pytest(
        [
            str(Path("zsiga/harness/behavioral")),
        ],
        output_path=output_path,
    )


def run_regression(
    output_path: str = "harness-results.jsonl",
) -> list[TestReport]:
    """Execute the full project regression test suite.

    Returns:
        A list of :class:`TestReport` instances, one per test item.
    """
    runner = HarnessRunner()
    return runner.run_pytest(["tests/"], output_path=output_path)


def run_qualification(
    output_path: str = "harness-results.jsonl",
) -> QualificationReport:
    """Run both capability and regression suites and return a combined report.

    Returns:
        A :class:`QualificationReport` with capability_results,
        regression_results, and an overall ``passed`` flag.
    """
    output_file = Path(output_path)
    if output_file.exists():
        output_file.unlink()

    cap_reports = run_capability_tests(output_path=output_path)
    reg_reports = run_regression(output_path=output_path)
    all_reports = cap_reports + reg_reports
    all_passed = bool(all_reports) and all(r.status == "passed" for r in all_reports)
    return QualificationReport(
        capability_results=cap_reports,
        regression_results=reg_reports,
        passed=all_passed,
    )


__all__ = [
    "PhaseContractResult",
    "PhaseContractHarness",
    "PhaseContractError",
    "ContractViolation",
    "HarnessResult",
    "HarnessRunner",
    "MockLLMClient",
    "MockTransport",
    "QualificationReport",
    "TempGitRepo",
    "TestError",
    "TestEvent",
    "TestFailed",
    "TestPassed",
    "TestReport",
    "TestStarted",
    "mock_llm_client",
    "mock_transport",
    "run_capability_tests",
    "run_qualification",
    "run_regression",
    "temp_git_repo",
]
