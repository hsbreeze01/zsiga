# daemon-test-file

## ADDED Requirements

### Requirement: Daemon test file structure

The test file `tests/test_daemon.py` SHALL exist and contain direct unit tests for
functions in `zsiga/daemon.py` that are not covered by existing test files
(`test_daemon_state.py`, `test_daemon_cycle_resilience.py`, `test_daemon_scheduling.py`).

#### Scenario: Test file exists and is importable

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the project test directory `tests/`
- **When** pytest discovers test files
- **Then** `tests/test_daemon.py` exists and contains at least 8 `def test_` functions

#### Scenario: Contains BAC-02 required test function names

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the contents of `tests/test_daemon.py`
- **When** inspecting the file for function definitions
- **Then** the file contains functions named `test__lock_path`, `test__daemon_state_path`, and `test__read_daemon_state`

#### Scenario: All tests pass with exit code 0

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** `tests/test_daemon.py` exists with valid test functions
- **When** running `python -m pytest tests/test_daemon.py -x`
- **Then** the exit code is 0 and no tests fail
