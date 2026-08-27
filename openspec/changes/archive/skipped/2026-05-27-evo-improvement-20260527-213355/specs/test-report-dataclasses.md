# test-report-dataclasses

## ADDED Requirements

### Requirement: TestReport dataclass construction

`TestReport` SHALL be a frozen-compatible dataclass with four fields:
`name` (str), `status` (str, one of `"passed"`, `"failed"`, `"error"`),
`duration_s` (float), and `message` (str).

The class SHALL set `__test__ = False` to prevent pytest from collecting it
as a test class.

#### Scenario: TestReport stores all fields correctly

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport

- **Given** a `TestReport` constructed with `name="pkg::test_a"`,
  `status="passed"`, `duration_s=0.42`, `message=""`
- **When** each field is read back
- **Then** all four fields equal their construction values

#### Scenario: TestReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport

- **Given** the `TestReport` class
- **When** `TestReport.__test__` is inspected
- **Then** it SHALL equal `False`

### Requirement: QualificationReport dataclass construction

`QualificationReport` SHALL be a dataclass with three fields:
`capability_results` (list of `TestReport`), `regression_results` (list of
`TestReport`), and `passed` (bool).

The class SHALL set `__test__ = False`.

#### Scenario: QualificationReport with all-passing results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** a `QualificationReport` with `capability_results` containing two
  `TestReport(status="passed")` entries, `regression_results` containing one
  `TestReport(status="passed")`, and `passed=True`
- **When** the `passed` field is read
- **Then** it SHALL be `True`

#### Scenario: QualificationReport with a failing result

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** a `QualificationReport` with one `TestReport(status="failed")`
  in `regression_results` and `passed=False`
- **When** the `passed` field is read
- **Then** it SHALL be `False`

#### Scenario: QualificationReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** the `QualificationReport` class
- **When** `QualificationReport.__test__` is inspected
- **Then** it SHALL equal `False`
