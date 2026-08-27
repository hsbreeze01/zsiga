# runner-test-coverage

> Delta spec for evo-improvement-20260530-082547
> ⚠️ See clarify.md overlap warning — `tests/test_harness_runner.py` already provides full coverage.

## ADDED Requirements

### Requirement: Runner module smoke test file

A new test file `tests/test_runner.py` SHALL exist and contain mechanically
verifiable smoke tests for `zsiga.harness.runner` public symbols.

#### Scenario: Test file exists on disk

- **testable**: true
- **target**: tests/test_runner.py
- **Given** the project test directory
- **When** checking for `tests/test_runner.py`
- **Then** the file SHALL exist

#### Scenario: Test file contains module import test

- **testable**: true
- **target**: tests/test_runner.py::test_module_import
- **Given** `tests/test_runner.py` exists
- **When** searching for a function named `test_module_import`
- **Then** the function SHALL be present and SHALL import
  `zsiga.harness.runner` without error

#### Scenario: Test file contains module smoke test

- **testable**: true
- **target**: tests/test_runner.py::test_module_smoke
- **Given** `tests/test_runner.py` exists
- **When** searching for a function named `test_module_smoke`
- **Then** the function SHALL be present and SHALL assert that
  public symbols (TestEvent, HarnessRunner, HarnessResult, etc.)
  are accessible from the module namespace

#### Scenario: All tests pass under pytest

- **testable**: true
- **target**: tests/test_runner.py
- **Given** `tests/test_runner.py` exists with at least one `def test_` function
- **When** running `python -m pytest tests/test_runner.py`
- **Then** the exit code SHALL be 0

### Requirement: Dataclass family construction tests

The test file SHALL verify that the runner module's event dataclasses
construct correctly and expose expected fields.

#### Scenario: Event dataclasses are constructable

- **testable**: true
- **target**: tests/test_runner.py::test_event_dataclasses_constructable
- **Given** the runner module is imported
- **When** constructing TestEvent(`test_name`, `timestamp`), TestStarted,
  TestPassed(`+duration_ms`), TestFailed(`+error_message`), TestError(`+error_message`)
  with valid arguments
- **Then** each instance SHALL expose the provided field values without error

### Requirement: Aggregate data class tests

The test file SHALL verify that HarnessResult, TestReport, and
QualificationReport aggregate data correctly.

#### Scenario: HarnessResult aggregates reports

- **testable**: true
- **target**: tests/test_runner.py::test_harness_result_aggregation
- **Given** HarnessResult is imported from `zsiga.harness.runner`
- **When** constructing a HarnessResult with `total`, `passed`, `failed`,
  `errors`, and `events` (a list of TestEvent instances)
- **Then** the `events` attribute SHALL contain the provided list

### Requirement: HarnessRunner mock-isolated tests

The test file SHALL contain tests for HarnessRunner's core methods
(`discover`, `run`, `run_pytest`) using mock isolation so that no
real subprocess or filesystem access occurs.

#### Scenario: HarnessRunner discover with mocked filesystem

- **testable**: false
- **Given** HarnessRunner is imported and filesystem is mocked
- **When** calling `HarnessRunner.discover()` with a mock directory
- **Then** it SHALL return a list of discovered test paths without
  performing real I/O

> Note: Mock-isolated tests depend on internal implementation details
> and cannot be mechanically verified by a static spec test.

## MODIFIED Requirements

_None._

## REMOVED Requirements

_None._
