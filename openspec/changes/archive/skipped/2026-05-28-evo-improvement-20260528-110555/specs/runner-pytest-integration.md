# runner-pytest-integration

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest delegates to pytest.main

`HarnessRunner.run_pytest(test_paths, output_path)` SHALL invoke `pytest.main()` with the provided test paths and a `_HarnessCollectorPlugin` instance. It SHALL return a `list[TestReport]` collected by the plugin.

#### Scenario: run_pytest returns reports for passing tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** `pytest.main` is mocked to invoke the plugin's `pytest_runtest_logreport` with a call-phase passed report (`when="call"`, `passed=True`, `nodeid="test_ok.py::test_ok"`, `duration=0.1`)
- **When** `HarnessRunner().run_pytest(["tests/test_ok.py"])` is called
- **Then** the return value SHALL be a non-empty `list[TestReport]` with `status="passed"`

#### Scenario: run_pytest returns empty list for empty paths

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** an empty `test_paths` list and `pytest.main` is mocked (returns 0)
- **When** `HarnessRunner().run_pytest([])` is called
- **Then** the return value SHALL be an empty `list` (no tests collected, no reports)

#### Scenario: run_pytest passes correct arguments to pytest.main

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** `pytest.main` is mocked to capture its arguments
- **When** `HarnessRunner().run_pytest(["tests/test_foo.py"], output_path="/tmp/out.jsonl")` is called
- **Then** `pytest.main` SHALL be called with `args` containing `"tests/test_foo.py"`, `"-p"`, `"no:cacheprovider"`, and `"--tb=short"`, and `plugins` list containing an `_HarnessCollectorPlugin` with `output_path="/tmp/out.jsonl"`

#### Scenario: run_pytest creates JSONL output file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary output path and `pytest.main` is mocked to invoke the plugin's `pytest_runtest_logreport` with a call-phase passed report
- **When** `HarnessRunner().run_pytest(["tests/test_a.py"], output_path=str(jsonl_path))` is called
- **Then** the JSONL output file SHALL exist and contain at least one valid JSON line with keys `name`, `status`, `duration_s`, `message`, `timestamp`
