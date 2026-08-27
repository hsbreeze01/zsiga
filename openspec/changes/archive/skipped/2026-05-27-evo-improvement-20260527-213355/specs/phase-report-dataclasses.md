# phase-report-dataclasses.md

## ADDED Requirements

### Requirement: TestReport dataclass construction and field semantics

The `TestReport` dataclass SHALL expose four fields: `name` (str), `status` (str, one of "passed"/"failed"/"error"), `duration_s` (float), and `message` (str).  Construction with positional or keyword arguments MUST succeed.  The `__test__` class attribute SHALL be `False` to prevent pytest collection.

#### Scenario: TestReport constructed with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` dataclass is imported
- **When** `TestReport(name="foo::test_bar", status="passed", duration_s=0.123, message="")` is constructed
- **Then** the resulting object has `.name == "foo::test_bar"`, `.status == "passed"`, `.duration_s == 0.123`, `.message == ""`

#### Scenario: TestReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` class
- **When** `TestReport.__test__` is accessed
- **Then** it equals `False`

---

### Requirement: QualificationReport dataclass with aggregated pass verdict

The `QualificationReport` dataclass SHALL expose three fields: `capability_results` (list of TestReport), `regression_results` (list of TestReport), and `passed` (bool).  The `passed` field is stored explicitly — it is `True` only when every TestReport across both lists has `status == "passed"`.

#### Scenario: QualificationReport all-passing

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** two TestReport objects both with `status="passed"`
- **When** `QualificationReport(capability_results=[r1], regression_results=[r2], passed=True)` is constructed
- **Then** `.passed` is `True` and both result lists contain one element each

#### Scenario: QualificationReport with mixed results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a passing TestReport and a failing TestReport
- **When** `QualificationReport(capability_results=[passing], regression_results=[failing], passed=False)` is constructed
- **Then** `.passed` is `False`

#### Scenario: QualificationReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** the `QualificationReport` class
- **When** `QualificationReport.__test__` is accessed
- **Then** it equals `False`
