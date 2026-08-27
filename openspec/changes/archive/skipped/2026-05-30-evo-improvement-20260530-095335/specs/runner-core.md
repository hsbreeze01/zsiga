# runner-core.md

## ADDED Requirements

### Requirement: HarnessRunner discover finds test_*.py files

The test file `tests/test_runner.py` SHALL verify that `HarnessRunner.discover()`
locates only files matching `test_*.py` in the given directory and raises
`FileNotFoundError` for non-existent paths.

#### Scenario: Discover finds test_*.py and ignores non-test files

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a temporary directory containing `test_alpha.py`, `test_beta.py`,
  and `helper.py`
- **When** `HarnessRunner().discover(temp_dir)` is called
- **Then** the returned list SHALL contain exactly `test_alpha.py` and
  `test_beta.py`, and SHALL NOT contain `helper.py`

#### Scenario: Discover raises FileNotFoundError for missing directory

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a path `/nonexistent/dir/xyz` that does not exist
- **When** `HarnessRunner().discover("/nonexistent/dir/xyz")` is called
- **Then** it SHALL raise `FileNotFoundError`

#### Scenario: Discover returns empty list for directory with no test files

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** an empty temporary directory
- **When** `HarnessRunner().discover(empty_dir)` is called
- **Then** the returned list SHALL be empty

### Requirement: HarnessRunner run executes discovered tests and emits events

The test file `tests/test_runner.py` SHALL verify that `HarnessRunner.run()`
executes discovered test functions, records correct pass/fail/error counts,
and emits the appropriate event types.

#### Scenario: Run reports passed count for passing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with a file `test_ok.py` containing
  `def test_ok(): assert True`
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** the `HarnessResult.passed` SHALL equal `1` and `failed` SHALL equal `0`

#### Scenario: Run reports failed count for failing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with a file `test_bad.py` containing
  `def test_bad(): assert False`
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** the `HarnessResult.failed` SHALL equal `1` and `passed` SHALL equal `0`

#### Scenario: Run reports errors count for test raising RuntimeError

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with a file `test_err.py` containing
  `def test_boom(): raise RuntimeError("unexpected")`
- **When** `HarnessRunner().discover(dir).run()` is called
- **Then** the `HarnessResult.errors` SHALL equal `1`

#### Scenario: Run without prior discover returns zero-count result

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a fresh `HarnessRunner()` with no prior `discover()` call
- **When** `runner.run()` is called
- **Then** the result SHALL have `total == 0`, `passed == 0`, `failed == 0`,
  `errors == 0`

### Requirement: HarnessRunner results property returns last run result

The test file `tests/test_runner.py` SHALL verify that the `results` property
reflects the most recent `HarnessResult` from `run()`.

#### Scenario: Results property returns HarnessResult after run

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.results

- **Given** a `HarnessRunner` that has discovered and run a single passing test
- **When** `runner.results` is accessed
- **Then** it SHALL return a `HarnessResult` with `total == 1` and `passed == 1`

### Requirement: HarnessRunner run_pytest integrates with pytest.main

The test file `tests/test_runner.py` SHALL verify that `run_pytest()` returns
a list of `TestReport` objects and handles edge cases such as empty test
files (no collected items).

#### Scenario: run_pytest returns error report for file with no tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory with a file `test_empty.py` containing only
  a comment `# no tests`
- **When** `HarnessRunner().run_pytest([str(test_file)], str(output_path))` is called
- **Then** the returned reports SHALL include at least one entry with
  `status == "error"` and message containing `"no executable test results"`

#### Scenario: run_pytest creates JSONL output file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory with a file `test_pass.py` containing
  `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_file)], str(output_path))` is called
- **Then** the file at `output_path` SHALL exist and each line SHALL be valid JSON
  containing `name`, `status`, `duration_s`, `message`, and `timestamp` keys
