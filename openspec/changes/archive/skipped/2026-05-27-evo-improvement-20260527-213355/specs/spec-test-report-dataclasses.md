# spec-test-report-dataclasses

## ADDED Requirements

### Requirement: TestReport dataclass construction

The `TestReport` dataclass SHALL expose four fields: `name` (str), `status` (str — one of "passed", "failed", "error"), `duration_s` (float), and `message` (str). All fields are required positional arguments with no defaults.

The `__test__` class attribute SHALL be `False` to prevent pytest collection.

#### Scenario: Construct a passed TestReport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::TestReport

- **Given** a TestReport is constructed with `name="test_foo::test_bar"`, `status="passed"`, `duration_s=0.123`, `message=""`
- **When** the instance fields are accessed
- **Then** `name == "test_foo::test_bar"`, `status == "passed"`, `duration_s == 0.123`, `message == ""`

#### Scenario: Construct a failed TestReport with error message

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::TestReport

- **Given** a TestReport is constructed with `name="mod::test_x"`, `status="failed"`, `duration_s=1.5`, `message="AssertionError: expected 1"`
- **When** the instance fields are accessed
- **Then** `status == "failed"` and `message == "AssertionError: expected 1"`

#### Scenario: TestReport is not collected by pytest

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::TestReport

- **Given** the TestReport class
- **When** its `__test__` attribute is read
- **Then** it SHALL equal `False`

---

### Requirement: QualificationReport dataclass construction

The `QualificationReport` dataclass SHALL expose three fields: `capability_results` (list of TestReport), `regression_results` (list of TestReport), and `passed` (bool).

The `passed` field is a plain bool stored at construction time — it is NOT a computed property. The `__test__` class attribute SHALL be `False`.

#### Scenario: Construct QualificationReport with all-passed results

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** two TestReport instances with `status="passed"` are created
- **When** a QualificationReport is constructed with those as capability_results and regression_results, `passed=True`
- **Then** `passed == True` and both lists have length 1

#### Scenario: QualificationReport passed=False when any test failed

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** one TestReport with `status="passed"` and one with `status="failed"`
- **When** a QualificationReport is constructed with `passed=False`, the failed report in capability_results
- **Then** `passed == False`

#### Scenario: QualificationReport is not collected by pytest

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** the QualificationReport class
- **When** its `__test__` attribute is read
- **Then** it SHALL equal `False`

