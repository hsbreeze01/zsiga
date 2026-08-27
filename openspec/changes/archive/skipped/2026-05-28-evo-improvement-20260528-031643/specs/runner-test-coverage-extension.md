# runner-test-coverage-extension

> Extends `tests/test_harness_runner.py` with tests covering previously
> untested interfaces in `zsiga/harness/runner.py`.

## MODIFIED Requirements

_(No existing requirements are changed. Tests are appended to the existing
test file without modifying any current test function.)_

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest() SHALL return TestReport list

`run_pytest()` invokes `pytest.main()` with a collector plugin and returns a
`list[TestReport]`. The caller MUST receive one `TestReport` per test item in
the "call" phase.

#### Scenario: run_pytest_with_single_passing_test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a single test file with one
  passing test function
- **When** `HarnessRunner().run_pytest([str(test_file)])` is called
- **Then** the returned list SHALL contain exactly one `TestReport` with
  `status == "passed"`

#### Scenario: run_pytest_with_single_failing_test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a single test file with one
  failing test function (`assert False`)
- **When** `HarnessRunner().run_pytest([str(test_file)])` is called
- **Then** the returned list SHALL contain exactly one `TestReport` with
  `status == "failed"` and a non-empty `message`

---

### Requirement: _HarnessCollectorPlugin SHALL filter and record test outcomes

`_HarnessCollectorPlugin` implements pytest hooks. It SHALL only record
reports from the `"call"` phase, creating `TestReport` objects with correct
status, duration, and message fields.

#### Scenario: logreport_ignores_setup_phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report whose
  `when == "setup"`
- **Then** the plugin's `reports` list SHALL remain empty

#### Scenario: logreport_records_passed_call

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report whose
  `when == "call"`, `passed == True`, `failed == False`, and
  `duration == 0.05`
- **Then** the plugin's `reports` list SHALL contain one `TestReport` with
  `status == "passed"`, `duration_s == 0.05`, and `message == ""`

#### Scenario: logreport_records_failed_call

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report whose
  `when == "call"`, `passed == False`, `failed == True`,
  `longrepr == "AssertionError"`, and `duration == 0.1`
- **Then** the plugin's `reports` list SHALL contain one `TestReport` with
  `status == "failed"` and `message == "AssertionError"`

#### Scenario: logreport_records_error_call

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report whose
  `when == "call"`, `passed == False`, `failed == False`,
  `longrepr == "RuntimeError"`
- **Then** the plugin's `reports` list SHALL contain one `TestReport` with
  `status == "error"` and `message == "RuntimeError"`

#### Scenario: logstart_records_timing

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart` is called with `nodeid == "test_a.py::test_one"`
- **Then** `plugin._start_times["test_a.py::test_one"]` SHALL be a positive
  float representing the current time

---

### Requirement: _HarnessCollectorPlugin._append_jsonl SHALL write valid JSONL

`_append_jsonl()` SHALL append one JSON line per report, containing the
fields `name`, `status`, `duration_s`, `message`, and `timestamp`.

#### Scenario: append_jsonl_creates_file_with_valid_line

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a
  non-existent file in a temporary directory
- **When** `_append_jsonl` is called with a `TestReport(name="t",
  status="passed", duration_s=0.1, message="")`
- **Then** the output file SHALL exist and contain exactly one line that is
  valid JSON with keys `name`, `status`, `duration_s`, `message`,
  `timestamp`; the file SHALL end with a newline

#### Scenario: append_jsonl_appends_multiple_lines

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with an existing JSONL file containing
  one line
- **When** `_append_jsonl` is called with a second `TestReport`
- **Then** the output file SHALL contain exactly two lines, each valid JSON

---

### Requirement: HarnessRunner._run_file() SHALL handle unloadable modules gracefully

When `_run_file()` encounters a module that cannot be loaded (`spec is None`
or `spec.loader is None`), it SHALL append a `TestError` event and increment
`errors` without crashing.

#### Scenario: run_file_null_spec_produces_test_error

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with a `HarnessResult` already initialized
- **When** `_run_file` is called with a path where
  `importlib.util.spec_from_file_location` returns `None` (via mock)
- **Then** the result SHALL have `errors == 1` and contain one `TestError`
  event with a non-empty `error_message` containing the file path

#### Scenario: run_file_exec_exception_produces_test_error

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with a `HarnessResult` already initialized
- **When** `_run_file` is called with a test file whose module-level code
  raises an exception during `exec_module`
- **Then** the result SHALL have `errors == 1` and contain one `TestError`
  event with a non-empty `error_message` containing the traceback

---

### Requirement: TestReport and QualificationReport SHALL satisfy their dataclass contracts

`TestReport` and `QualificationReport` are structured report dataclasses
used by `run_pytest()` and downstream consumers.

#### Scenario: test_report_field_contract

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** nothing
- **When** `TestReport(name="a", status="passed", duration_s=1.0, message="")`
  is constructed
- **Then** all four fields SHALL be accessible and match the constructor
  arguments

#### Scenario: qualification_report_passed

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** two `TestReport` lists where every report has `status ==
  "passed"`
- **When** `QualificationReport(capability_results=...,
  regression_results=..., passed=True)` is constructed
- **Then** `passed` SHALL be `True` and both result lists SHALL be non-empty

#### Scenario: qualification_report_with_failure

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a capability result list containing a report with `status ==
  "failed"`
- **When** `QualificationReport(..., passed=False)` is constructed
- **Then** `passed` SHALL be `False`
