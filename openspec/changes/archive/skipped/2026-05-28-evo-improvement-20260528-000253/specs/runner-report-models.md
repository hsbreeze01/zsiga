# runner-report-models

## ADDED Requirements

### Requirement: TestReport dataclass construction and pytest exclusion

`TestReport` SHALL preserve all construction fields (`name`, `status`,
`duration_s`, `message`) and SHALL set `__test__ = False` to prevent pytest
collection.

#### Scenario: TestReport construction preserves all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a `TestReport` constructed with `name="test_foo"`, `status="passed"`, `duration_s=0.123`, `message=""`
- **When** each field is accessed
- **Then** `name == "test_foo"`, `status == "passed"`, `duration_s == 0.123`, `message == ""`

#### Scenario: TestReport with failed status and error message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a `TestReport` constructed with `status="failed"` and a non-empty `message`
- **When** `status` and `message` fields are accessed
- **Then** `status == "failed"` and `message` contains the exact error string

#### Scenario: TestReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` class definition
- **When** `TestReport.__test__` is accessed
- **Then** the value is `False`

### Requirement: QualificationReport passed semantics

`QualificationReport` SHALL store `capability_results`, `regression_results`,
and a boolean `passed` field. The `passed` field is set by the caller; the
report does not compute it. `QualificationReport` SHALL set `__test__ = False`.

#### Scenario: QualificationReport with all-passed results and passed=True

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** capability and regression result lists where all statuses are `"passed"`
- **When** a `QualificationReport` is constructed with `passed=True`
- **Then** `passed is True` and both result lists contain the provided `TestReport` instances

#### Scenario: QualificationReport with mixed results and passed=False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a capability list containing a `"failed"` status report
- **When** a `QualificationReport` is constructed with `passed=False`
- **Then** `passed is False` and the capability list includes the failed report

#### Scenario: QualificationReport with empty results and passed=True

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** empty capability and regression result lists
- **When** a `QualificationReport` is constructed with `passed=True`
- **Then** `passed is True` and both result lists are empty

#### Scenario: QualificationReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** the `QualificationReport` class definition
- **When** `QualificationReport.__test__` is accessed
- **Then** the value is `False`
