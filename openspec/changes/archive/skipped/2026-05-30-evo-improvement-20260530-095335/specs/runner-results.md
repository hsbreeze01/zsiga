# runner-results.md

## ADDED Requirements

### Requirement: HarnessResult aggregation defaults and custom construction

The test file `tests/test_runner.py` SHALL verify that `HarnessResult`
initializes with zero counts and an empty events list, and accepts custom
values for all fields.

#### Scenario: HarnessResult defaults to all-zero counts and empty events

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult

- **Given** the module `zsiga.harness.runner` is importable
- **When** `HarnessResult()` is constructed with no arguments
- **Then** `total` equals `0`, `passed` equals `0`, `failed` equals `0`,
  `errors` equals `0`, and `events` equals `[]`

#### Scenario: HarnessResult accepts custom field values

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult

- **Given** the module `zsiga.harness.runner` is importable
- **When** `HarnessResult(total=10, passed=7, failed=2, errors=1)` is constructed
- **Then** `total` equals `10`, `passed` equals `7`, `failed` equals `2`,
  `errors` equals `1`, and `events` equals `[]`

#### Scenario: HarnessResult events list is independent between instances

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult

- **Given** two `HarnessResult` instances constructed with defaults
- **When** an event is appended to the first instance's `events` list
- **Then** the second instance's `events` list SHALL remain empty

### Requirement: TestReport dataclass fields

The test file `tests/test_runner.py` SHALL verify that `TestReport` stores
all four required fields correctly.

#### Scenario: TestReport stores name, status, duration_s, and message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestReport(name="t::test_a", status="passed", duration_s=0.5, message="")`
  is constructed
- **Then** `name` equals `"t::test_a"`, `status` equals `"passed"`,
  `duration_s` equals `0.5`, and `message` equals `""`

#### Scenario: TestReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport

- **Given** the `TestReport` class from `zsiga.harness.runner`
- **When** the class attribute `__test__` is inspected
- **Then** it SHALL equal `False`

### Requirement: QualificationReport combines capability and regression results

The test file `tests/test_runner.py` SHALL verify that `QualificationReport`
correctly stores two result lists and a boolean passed flag.

#### Scenario: QualificationReport with empty lists and passed=False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** the module `zsiga.harness.runner` is importable
- **When** `QualificationReport(capability_results=[], regression_results=[], passed=False)`
  is constructed
- **Then** `passed` SHALL equal `False`, `capability_results` SHALL equal `[]`,
  and `regression_results` SHALL equal `[]`

#### Scenario: QualificationReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** the `QualificationReport` class from `zsiga.harness.runner`
- **When** the class attribute `__test__` is inspected
- **Then** it SHALL equal `False`
