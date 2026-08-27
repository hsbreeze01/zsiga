# report-dataclasses-coverage

Extends `tests/test_harness_runner.py` with tests for the previously untested
`TestReport` and `QualificationReport` dataclasses.

## ADDED Requirements

### Requirement: TestReport stores structured test result

`TestReport` SHALL be a dataclass with fields `name`, `status`, `duration_s`,
and `message`. Instances SHALL be constructible and all fields SHALL be
accessible.

#### Scenario: TestReport construction and field access

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** nothing
- **When** `TestReport(name="test_a", status="passed", duration_s=0.42, message="")` is constructed
- **Then** `report.name == "test_a"`, `report.status == "passed"`, `report.duration_s == 0.42`, `report.message == ""`

#### Scenario: TestReport stores failed status

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** nothing
- **When** `TestReport(name="test_b", status="failed", duration_s=1.0, message="AssertionError")` is constructed
- **Then** `report.status == "failed"` and `report.message == "AssertionError"`

### Requirement: QualificationReport aggregates capability and regression results

`QualificationReport` SHALL contain `capability_results`, `regression_results`,
and a boolean `passed` field. The `passed` field is `True` only when ALL
individual reports have status `"passed"`.

#### Scenario: QualificationReport passed when all reports pass

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** two `TestReport` objects both with `status="passed"`
- **When** `QualificationReport(capability_results=[r1], regression_results=[r2], passed=True)` is constructed
- **Then** `report.passed is True` and `len(report.capability_results) == 1`

#### Scenario: QualificationReport with empty results lists

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** no test reports
- **When** `QualificationReport(capability_results=[], regression_results=[], passed=True)` is constructed
- **Then** `report.passed is True` and both result lists are empty
