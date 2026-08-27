# Delta Spec: Supplement Runner Test Coverage

## ADDED Requirements

### Requirement: Supplementary test coverage for harness runner module

`tests/test_harness_runner.py` SHALL be supplemented with additional test cases
to cover behavioral edge cases in `zsiga/harness/runner.py` that are not currently
exercised by the existing 18 test methods.

#### Scenario: TestEvent subclasses are not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestEvent
- **Given** the dataclass `TestEvent` and its subclasses `TestStarted`, `TestPassed`, `TestFailed`, `TestError` each have a class attribute `__test__` set to `False`
- **When** pytest scans the module `zsiga.harness.runner`
- **Then** pytest SHALL NOT attempt to collect any of these classes as test cases (verified by checking `__test__ is False`)

#### Scenario: HarnessRunner stores fixtures from constructor

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** a `HarnessRunner` instance created with `fixtures=["item_a", "item_b"]`
- **When** the constructor completes
- **Then** the runner SHALL store the fixtures list internally (verified by accessing `_fixtures` attribute)

#### Scenario: HarnessRunner defaults fixtures to empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** a `HarnessRunner` instance created with no arguments
- **When** the constructor completes
- **Then** `_fixtures` SHALL be an empty list

#### Scenario: run_pytest returns passed reports for passing tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary test file containing a passing test function `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_file)], str(output_path))` is called
- **Then** the returned list SHALL contain at least one `TestReport` with `status == "passed"` and `duration_s >= 0`

#### Scenario: run_pytest returns failed report for failing tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary test file containing a failing test `def test_fail(): assert False`
- **When** `HarnessRunner().run_pytest([str(test_file)], str(output_path))` is called
- **Then** the returned list SHALL contain at least one `TestReport` with `status == "failed"` and a non-empty `message`

#### Scenario: QualificationReport passed is True when all results passed

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` with `capability_results` and `regression_results` all having `status == "passed"`
- **When** the `passed` field is inspected
- **Then** `passed` SHALL be `True`

#### Scenario: QualificationReport passed is False when any result failed

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` where at least one result in `capability_results` or `regression_results` has `status != "passed"`
- **When** the `passed` field is inspected
- **Then** `passed` SHALL be `False`

#### Scenario: JSONL output contains valid JSON lines with required fields

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** `run_pytest` is called with a valid test file and an `output_path`
- **When** execution completes and the JSONL file is read
- **Then** each line SHALL be valid JSON containing keys `name`, `status`, `duration_s`, `message`, and `timestamp`

#### Scenario: TestReport accepts all valid status values

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** `TestReport` dataclass
- **When** instances are created with `status` values `"passed"`, `"failed"`, and `"error"`
- **Then** each instance SHALL store the provided status value without error

#### Scenario: HarnessResult events list accumulates entries

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult
- **Given** a `HarnessResult` with `events` containing 3 manually appended `TestEvent` instances
- **When** `len(result.events)` is evaluated
- **Then** it SHALL equal 3

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
