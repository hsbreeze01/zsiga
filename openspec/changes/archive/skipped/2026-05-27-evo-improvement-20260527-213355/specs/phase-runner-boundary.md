# phase-runner-boundary.md

## ADDED Requirements

### Requirement: HarnessRunner accepts optional fixtures list

`HarnessRunner.__init__` SHALL accept an optional `fixtures` parameter (list or None).  When `None` is passed, it MUST default to an empty list.  The fixtures list is stored internally but is not used during `discover` or `run` in the current implementation.

#### Scenario: HarnessRunner init with no arguments

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** `HarnessRunner` is imported
- **When** `HarnessRunner()` is constructed with no arguments
- **Then** `runner._fixtures` is an empty list and `runner._test_files` is an empty list

#### Scenario: HarnessRunner init with fixtures list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** `HarnessRunner` is imported
- **When** `HarnessRunner(fixtures=["foo"])` is constructed
- **Then** `runner._fixtures == ["foo"]`

---

### Requirement: HarnessRunner._run_file handles unloadable modules gracefully

When `_run_file` encounters a module whose `spec_from_file_location` returns `None` or whose `spec.loader` is `None`, it SHALL append a `TestError` event to results and increment `errors`, without raising an exception.

#### Scenario: _run_file with invalid module spec

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with a non-Python file in `_test_files` (e.g., a file that cannot be loaded as a module)
- **When** `_run_file` is called on that file
- **Then** `result.errors >= 1` and the last event in `result.events` is a `TestError`

---

### Requirement: HarnessRunner results property returns last run result

The `results` property SHALL return the `HarnessResult` from the most recent `run()` call.  Before any `run()` call, it SHALL return a default `HarnessResult` with all zeroes.

#### Scenario: results property before run

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.results
- **Given** a fresh `HarnessRunner` instance
- **When** `runner.results` is accessed without calling `run()`
- **Then** it returns a `HarnessResult` with `total == 0`, `passed == 0`, `failed == 0`, `errors == 0`
