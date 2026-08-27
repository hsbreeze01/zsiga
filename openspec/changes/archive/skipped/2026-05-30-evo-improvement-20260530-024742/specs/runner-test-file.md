# runner-test-file

> **NOTE**: `tests/test_harness_runner.py` (277 lines, 20+ test functions) already
> provides comprehensive coverage of `zsiga/harness/runner.py`. This spec creates a
> supplementary `tests/test_runner.py` with import/smoke tests as specified by the
> proposal. The two files will coexist without conflict.

## ADDED Requirements

### Requirement: Runner module test file

The project SHALL contain a test file `tests/test_runner.py` that validates
`zsiga.harness.runner` module-level importability and basic class instantiation.

#### Scenario: test file exists

- **testable**: true
- **target**: tests/test_runner.py
- **Given** the project test directory `tests/`
- **When** checking for file `tests/test_runner.py`
- **Then** the file SHALL exist

#### Scenario: module import test function

- **testable**: true
- **target**: tests/test_runner.py::test_module_import
- **Given** the file `tests/test_runner.py` exists
- **When** inspecting the top-level definitions in the file
- **Then** a function named `test_module_import` SHALL exist and SHALL import
  `zsiga.harness.runner` successfully without raising an exception

#### Scenario: module smoke test function

- **testable**: true
- **target**: tests/test_runner.py::test_module_smoke
- **Given** the file `tests/test_runner.py` exists
- **When** inspecting the top-level definitions in the file
- **Then** a function named `test_module_smoke` SHALL exist and SHALL verify
  that key public classes (`TestEvent`, `TestStarted`, `TestPassed`, `TestFailed`,
  `TestError`, `HarnessResult`, `HarnessRunner`, `TestReport`, `QualificationReport`)
  are importable from `zsiga.harness.runner`

### Requirement: No regression to existing tests

The new test file SHALL NOT break any existing test file in the project.

#### Scenario: existing harness runner tests still pass

- **testable**: true
- **target**: tests/test_harness_runner.py
- **Given** the existing file `tests/test_harness_runner.py`
- **When** running `python -m pytest tests/test_harness_runner.py`
- **Then** the exit code SHALL be 0

#### Scenario: new test file passes pytest

- **testable**: true
- **target**: tests/test_runner.py
- **Given** the file `tests/test_runner.py` exists
- **When** running `python -m pytest tests/test_runner.py`
- **Then** the exit code SHALL be 0
