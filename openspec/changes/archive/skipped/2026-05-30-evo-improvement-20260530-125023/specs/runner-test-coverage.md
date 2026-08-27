# Spec: runner-test-coverage

> **Note**: `tests/test_harness_runner.py` already provides 28 tests covering all 10 classes
> in `zsiga/harness/runner.py`. This spec describes the **additional** `tests/test_runner.py`
> file requested by the proposal. The executor SHOULD verify whether the existing file
> already satisfies these requirements before creating a redundant one.

## ADDED Requirements

### Requirement: Runner module test file

The project SHALL contain a test file `tests/test_runner.py` that exercises the public API
of `zsiga/harness/runner.py`.

#### Scenario: test file exists

- **testable**: true
- **target**: tests/test_runner.py
- **Given** the project test directory
- **When** checking for file existence
- **Then** `tests/test_runner.py` exists on disk

#### Scenario: module import test present

- **testable**: true
- **target**: tests/test_runner.py::test_module_import
- **Given** `tests/test_runner.py` exists
- **When** parsing the file's AST
- **Then** it contains a function named `test_module_import` that successfully imports
  `zsiga.harness.runner`

#### Scenario: smoke test present

- **testable**: true
- **target**: tests/test_runner.py::test_module_smoke
- **Given** `tests/test_runner.py` exists
- **When** parsing the file's AST
- **Then** it contains a function named `test_module_smoke` that performs at least one
  non-trivial assertion against a symbol from `zsiga.harness.runner`

#### Scenario: all tests pass

- **testable**: true
- **target**: tests/test_runner.py
- **Given** `tests/test_runner.py` exists with at least one `test_` function
- **When** running `python -m pytest tests/test_runner.py`
- **Then** the exit code is 0 and no tests fail or error

### Requirement: Data-class coverage

`tests/test_runner.py` SHOULD cover the data-class layer of `zsiga/harness/runner.py`:

- `TestEvent` — base event dataclass (fields: `test_name`, `timestamp`)
- `TestStarted` — concrete event (inherits `test_name`, `timestamp`)
- `TestPassed` — adds `duration_ms`
- `TestFailed` — adds `duration_ms`, `error_message`
- `TestError` — adds `error_message`
- `HarnessResult` — aggregate result (fields: `total`, `passed`, `failed`, `errors`, `events`)
- `TestReport` — individual test report (fields: `name`, `status`, `duration_s`, `message`)
- `QualificationReport` — qualification-level report

#### Scenario: HarnessResult counting

- **testable**: true
- **target**: tests/test_runner.py
- **Given** `HarnessResult` from `zsiga.harness.runner` with fields `total`, `passed`, `failed`, `errors`
- **When** constructing a `HarnessResult(total=4, passed=3, failed=1, errors=0)`
- **Then** `total` equals 4

#### Scenario: TestStarted event construction

- **testable**: true
- **target**: tests/test_runner.py
- **Given** `TestStarted` from `zsiga.harness.runner` with fields `test_name`, `timestamp`
- **When** constructing a `TestStarted(test_name="test_foo", timestamp=1.0)`
- **Then** the `test_name` attribute equals `"test_foo"`

### Requirement: HarnessRunner method coverage

`tests/test_runner.py` SHOULD cover the `HarnessRunner` class's core methods with
appropriate mocking of subprocess/file-system dependencies.

#### Scenario: discover returns test files

- **testable**: true
- **target**: tests/test_runner.py
- **Given** a temporary directory containing two files matching `test_*.py` and one non-test file
- **When** `HarnessRunner().discover(directory)` is called with that directory path
- **Then** the returned list has length 2

#### Scenario: discover handles missing directory

- **testable**: true
- **target**: tests/test_runner.py
- **Given** a non-existent directory path
- **When** `HarnessRunner().discover(path)` is called
- **Then** it raises `FileNotFoundError`

## MODIFIED Requirements

_None_

## REMOVED Requirements

_None_
