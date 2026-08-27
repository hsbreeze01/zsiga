# runner-run-file-edge-cases

## ADDED Requirements

### Requirement: _run_file handles module-level import errors gracefully

When `spec.loader.exec_module(module)` raises an exception (e.g., the test file
contains a module-level `import` of a non-existent package), `_run_file` SHALL
append a `TestError` event to the result, increment `errors` by 1, and return
early without attempting to discover or execute any `test_*` functions within
the module.

The `TestError` event SHALL have `test_name` equal to the module's stem name
and a non-empty `error_message` containing the traceback.

#### Scenario: test file with module-level import error produces TestError

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a temporary directory containing a file `test_import_error.py` whose body is `import nonexistent_module_xyz`, and a `HarnessRunner` that has discovered this file
- **When** `runner.run()` is called
- **Then** the result SHALL have `errors == 1`, `passed == 0`, `failed == 0`, and `result.events` SHALL contain exactly one `TestError` event with `test_name == "test_import_error"` and a non-empty `error_message`

---

### Requirement: _run_file filters non-callable test_ attributes

When a test module contains attributes whose names start with `test_` but are
not callable (e.g., `test_count = 5`), `_run_file` SHALL skip those attributes
and only execute callable ones.

#### Scenario: module with non-callable test_ attribute is skipped

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a temporary directory containing a file `test_mixed.py` whose body defines `test_count = 5` and `def test_ok(): pass`
- **When** `runner.run()` is called
- **Then** the result SHALL have `passed == 1`, `errors == 0`, `failed == 0`, and `result.events` SHALL contain no events referencing `test_count`

---

### Requirement: _run_file processes mixed outcomes within a single file

When a single test module contains multiple `test_*` functions with different
outcomes (pass, fail via AssertionError, error via other Exception), `_run_file`
SHALL correctly classify each function independently and update the appropriate
counters.

#### Scenario: single file with passing, failing, and erroring tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a temporary directory containing a file `test_all.py` whose body defines `def test_ok(): pass`, `def test_fail(): assert False`, and `def test_err(): raise RuntimeError("boom")`
- **When** `runner.run()` is called
- **Then** the result SHALL have `passed == 1`, `failed == 1`, `errors == 1`, `total == 1`, and `result.events` SHALL contain at least one `TestPassed`, one `TestFailed`, and one `TestError` event

---

### Requirement: run resets state on each invocation

Calling `run()` SHALL create a fresh `HarnessResult` each time, resetting all
counters and events. Results from a previous `run()` call SHALL NOT accumulate
into subsequent calls.

#### Scenario: run called twice with different test sets produces independent results

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run
- **Given** a `HarnessRunner` with a temporary directory containing `test_a.py` that has a single passing test
- **When** `runner.discover(tmp_path)` is called, then `runner.run()` is called (first run), then `runner._test_files` is cleared, then `runner.run()` is called again (second run)
- **Then** the first `run()` result SHALL have `passed == 1`, and the second `run()` result SHALL have `total == 0`, `passed == 0`, `events == []`

---

### Requirement: _run_file emits events in correct order per test function

For each `test_*` function executed, `_run_file` SHALL emit a `TestStarted`
event first, followed by exactly one of `TestPassed`, `TestFailed`, or
`TestError`. The `TestStarted` event SHALL appear before its corresponding
result event in the `result.events` list.

#### Scenario: event order is TestStarted then TestPassed for a passing test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a temporary directory containing a file `test_order.py` that defines `def test_ok(): pass`
- **When** `runner.discover(tmp_path)` and `runner.run()` are called
- **Then** `result.events` SHALL have exactly two events, the first being a `TestStarted` instance and the second being a `TestPassed` instance, and both SHALL have the same `test_name`

#### Scenario: event order is TestStarted then TestFailed for a failing test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a temporary directory containing a file `test_order_fail.py` that defines `def test_bad(): assert False`
- **When** `runner.discover(tmp_path)` and `runner.run()` are called
- **Then** `result.events` SHALL have exactly two events, the first being a `TestStarted` instance and the second being a `TestFailed` instance, and both SHALL have the same `test_name`
