# runner-report-dataclasses

## ADDED Requirements

### Requirement: TestReport dataclass structure

The `TestReport` dataclass SHALL represent a single test result with four fields:
`name` (str), `status` (str, one of "passed"/"failed"/"error"), `duration_s` (float),
and `message` (str). The class MUST set `__test__ = False` to prevent pytest collection.

#### Scenario: Construct TestReport with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a TestReport is constructed with name="test_a", status="passed", duration_s=0.5, message=""
- **When** all fields are accessed
- **Then** each field equals its constructor argument

#### Scenario: TestReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the TestReport class attribute `__test__`
- **When** its value is inspected
- **Then** it SHALL be `False`

#### Scenario: TestReport with failure status and message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a TestReport is constructed with status="failed" and message="assert False"
- **When** the status and message fields are accessed
- **Then** status is "failed" and message is "assert False"

---

### Requirement: QualificationReport dataclass structure

The `QualificationReport` dataclass SHALL aggregate results from capability and
regression test suites. It MUST contain `capability_results` (list of TestReport),
`regression_results` (list of TestReport), and `passed` (bool). The `passed` field
SHOULD be `True` only when every TestReport in both lists has status "passed".
The class MUST set `__test__ = False` to prevent pytest collection.

#### Scenario: Construct QualificationReport with all passing results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a QualificationReport with capability_results containing one passed TestReport and regression_results containing one passed TestReport, passed=True
- **When** all fields are accessed
- **Then** capability_results has length 1, regression_results has length 1, and passed is True

#### Scenario: QualificationReport with empty result lists

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a QualificationReport with empty capability_results and regression_results, passed=True
- **When** both list fields are inspected
- **Then** capability_results is an empty list and regression_results is an empty list

#### Scenario: QualificationReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** the QualificationReport class attribute `__test__`
- **When** its value is inspected
- **Then** it SHALL be `False`
