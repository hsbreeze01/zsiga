# harness-runner-run

## ADDED Requirements

### Requirement: HarnessRunner.run Test Execution

The test file `tests/test_runner.py` SHALL contain unit tests for
`HarnessRunner.run()` covering passing tests, failing tests (AssertionError),
error tests (unexpected exceptions), multi-file execution, and the `results`
property, using `tmp_path` with dynamically written test modules for isolation.

#### Scenario: Run emits TestStarted and TestPassed for passing test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with a file `test_ok.py` containing `def test_ok(): assert True`
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** `result.total == 1`, `result.passed == 1`, and events contain one `TestStarted` and one `TestPassed`

#### Scenario: Run emits TestFailed for assertion failure

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with `test_bad.py` containing `def test_bad(): assert False`
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** `result.failed == 1` and events contain a `TestFailed` with non-empty `error_message`

#### Scenario: Run emits TestError for unexpected exception

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with `test_err.py` containing `def test_err(): raise RuntimeError("boom")`
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** `result.errors == 1` and events contain a `TestError`

#### Scenario: Run handles multiple files with mixed outcomes

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with two test files: one passing, one failing
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** `result.total == 2`, `result.passed == 1`, `result.failed == 1`

#### Scenario: Run without prior discover returns empty result

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a fresh `HarnessRunner()` with no discover call
- **When** `runner.run()` is called
- **Then** `result.total == 0`, `result.passed == 0`, `result.events == []`

#### Scenario: Results property reflects last run

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.results

- **Given** a `HarnessRunner` that has discovered and run one passing test
- **When** `runner.results` is accessed
- **Then** it returns the same `HarnessResult` as returned by `run()`

#### Scenario: Event timestamps are positive floats

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with a passing test file
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** every event in `result.events` has `.timestamp > 0`
