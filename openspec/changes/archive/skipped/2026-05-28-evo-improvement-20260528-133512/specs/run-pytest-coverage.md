# run_pytest Integration Test Coverage

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest invokes pytest and returns TestReport list

`HarnessRunner.run_pytest(test_paths, output_path)` SHALL accept a list of
path strings and an optional JSONL output path (default `"harness-results.jsonl"`).
It MUST invoke `pytest.main()` with the supplied paths plus flags
`-p no:cacheprovider --tb=short` and return a `list[TestReport]`.

#### Scenario: run_pytest on a passing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory containing `test_ok.py` with a passing test function
- **When** `HarnessRunner().run_pytest(["<path>/test_ok.py"], output_path="<path>/out.jsonl")` is called
- **Then** the returned list SHALL contain at least one `TestReport` with `status="passed"`

#### Scenario: run_pytest on a failing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory containing `test_fail.py` with `assert False`
- **When** `HarnessRunner().run_pytest(["<path>/test_fail.py"], output_path="<path>/out.jsonl")` is called
- **Then** the returned list SHALL contain at least one `TestReport` with `status="failed"`

#### Scenario: run_pytest writes JSONL output file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory containing a passing test file
- **When** `run_pytest` is called with a specific `output_path`
- **Then** the file at `output_path` SHALL exist
- **And** each line SHALL be valid JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`
