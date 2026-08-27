# runner-pytest-normal-path

## ADDED Requirements

### Requirement: run_pytest normal pass/fail scenarios

`HarnessRunner.run_pytest()` SHALL return a `list[TestReport]` where each report
accurately reflects the outcome of each individual test item executed by pytest.

- When all test items pass, every returned `TestReport.status` SHALL be `"passed"`.
- When one or more test items fail via assertion, the corresponding `TestReport`
  SHALL have `status="failed"` with a non-empty `message` containing the failure traceback.
- The returned list SHALL contain exactly one `TestReport` per test item collected
  by pytest (not counting harness-level error reports).

#### Scenario: run_pytest with all-passing tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a `test_pass.py` with two passing test functions `test_a` and `test_b`
- **When** `HarnessRunner().run_pytest([str(test_file)], str(jsonl_path))` is called
- **Then** the returned list contains exactly 2 `TestReport` objects, both with `status == "passed"`, each with a unique `name` matching the test item nodeid

#### Scenario: run_pytest with one failing test among passing tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a `test_mixed.py` with one passing test `test_ok` (assert True) and one failing test `test_bad` (assert False)
- **When** `HarnessRunner().run_pytest([str(test_file)], str(jsonl_path))` is called
- **Then** the returned list contains exactly 2 `TestReport` objects: one with `status == "passed"` and one with `status == "failed"` whose `message` is a non-empty string

#### Scenario: run_pytest produces JSONL output file with one line per test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a `test_simple.py` with one passing test `test_ok`
- **When** `HarnessRunner().run_pytest([str(test_file)], str(jsonl_path))` is called
- **Then** `jsonl_path` exists and contains exactly 1 non-empty line that is valid JSON with keys `"name"`, `"status"`, `"duration_s"`, `"message"`, and `"timestamp"`
