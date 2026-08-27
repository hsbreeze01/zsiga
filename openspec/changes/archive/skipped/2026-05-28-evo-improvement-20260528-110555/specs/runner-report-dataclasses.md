# runner-report-dataclasses

## ADDED Requirements

### Requirement: TestReport dataclass field contract

`TestReport` SHALL be a dataclass with fields `name` (str), `status` (str, one of "passed"/"failed"/"error"), `duration_s` (float), `message` (str).

`TestReport` SHALL set `__test__ = False` to prevent pytest from collecting it as a test class.

#### Scenario: TestReport construction with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a `TestReport` class is imported from `zsiga.harness.runner`
- **When** a `TestReport` is constructed with `name="test_foo"`, `status="passed"`, `duration_s=0.42`, `message=""`
- **Then** the resulting object has `.name == "test_foo"`, `.status == "passed"`, `.duration_s == 0.42`, `.message == ""`

#### Scenario: TestReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport.__test__
- **Given** the `TestReport` class from `zsiga.harness.runner`
- **When** `TestReport.__test__` is accessed
- **Then** the value SHALL be `False`

---

### Requirement: QualificationReport dataclass field contract

`QualificationReport` SHALL be a dataclass with fields `capability_results` (list[TestReport]), `regression_results` (list[TestReport]), and `passed` (bool).

`QualificationReport` SHALL set `__test__ = False`.

#### Scenario: QualificationReport with all passing results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` is constructed with `capability_results` containing one `TestReport(status="passed")` and `regression_results` containing one `TestReport(status="passed")`, and `passed=True`
- **When** the `passed` field is read
- **Then** it SHALL be `True`

#### Scenario: QualificationReport with mixed results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` is constructed with `capability_results` containing a `TestReport(status="passed")` and `regression_results` containing a `TestReport(status="failed")`, and `passed=False`
- **When** the `passed` field is read
- **Then** it SHALL be `False`

#### Scenario: QualificationReport with empty result lists

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` is constructed with empty `capability_results` and `regression_results`, and `passed=True`
- **When** the `passed` field is read
- **Then** it SHALL be `True` (no failures means qualification passes)

#### Scenario: QualificationReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport.__test__
- **Given** the `QualificationReport` class from `zsiga.harness.runner`
- **When** `QualificationReport.__test__` is accessed
- **Then** the value SHALL be `False`
