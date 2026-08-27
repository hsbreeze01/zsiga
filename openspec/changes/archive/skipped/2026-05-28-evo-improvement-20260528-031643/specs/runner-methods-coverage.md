# runner-methods-coverage

Extends `tests/test_harness_runner.py` with tests for previously uncovered
`HarnessRunner` methods and edge-case branches.

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest invokes pytest and returns reports

`HarnessRunner.run_pytest()` SHALL accept a list of test paths and an optional
output path, invoke `pytest.main()` with a `_HarnessCollectorPlugin`, and return
the plugin's collected `TestReport` list.

#### Scenario: run_pytest returns reports from invoked pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a passing test file `test_ok.py`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(tmp_path / "out.jsonl"))` is called
- **Then** the returned list contains at least one `TestReport` with `status == "passed"`

#### Scenario: run_pytest passes correct arguments to pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a `HarnessRunner` instance
- **When** `run_pytest(["some/path"])` is called (mocking `pytest.main`)
- **Then** `pytest.main` is called with arguments that include `"some/path"`, `"-p"`, `"no:cacheprovider"`, and `"--tb=short"`

### Requirement: HarnessRunner._run_file handles unloadable modules

When `_run_file` encounters a module whose `spec_from_file_location` returns
`None` or whose loader is `None`, it SHALL append a `TestError` event and
increment `errors` without raising.

#### Scenario: _run_file with null spec records error event

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with an initialised `_result` and a path to a file that cannot be loaded as a Python module (e.g., a binary file)
- **When** `_run_file(that_path)` is called
- **Then** `_result.errors` equals 1, and the last event in `_result.events` is a `TestError` with `error_message` containing `"Could not load module"`

#### Scenario: _run_file with module exec failure records error event

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with an initialised `_result` and a `.py` file whose body raises an exception at import time (e.g., `raise ImportError("nope")`)
- **When** `_run_file(that_path)` is called
- **Then** `_result.errors` equals 1, and the last event in `_result.events` is a `TestError` with `error_message` containing `"nope"`
