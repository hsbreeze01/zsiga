# runner-plugin-and-init

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin initial state

`_HarnessCollectorPlugin.__init__` SHALL initialize `reports` as an empty
list, `_start_times` as an empty dict, and store the provided `output_path`.

#### Scenario: Plugin initialized with empty reports and start_times

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.__init__
- **Given** a `_HarnessCollectorPlugin` constructed with `output_path="/tmp/out.jsonl"`
- **When** `reports` and `_start_times` are accessed
- **Then** `reports == []` and `_start_times == {}`

### Requirement: _HarnessCollectorPlugin pytest_runtest_logstart records time

`pytest_runtest_logstart` SHALL record the current time keyed by `nodeid`
in `_start_times`.

#### Scenario: pytest_runtest_logstart records start time

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_foo.py::test_bar", None)` is called
- **Then** `plugin._start_times["test_foo.py::test_bar"]` is a positive float

### Requirement: _HarnessCollectorPlugin pytest_runtest_logreport creates reports

`pytest_runtest_logreport` SHALL create a `TestReport` only for the `"call"`
phase. For `passed=True`, status SHALL be `"passed"`. For `failed=True`,
status SHALL be `"failed"` with `longrepr` as message. For neither passed nor
failed, status SHALL be `"error"`. Non-call phases SHALL be ignored.

#### Scenario: logreport creates passed report for call phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin with a mock report having `when="call"`, `passed=True`, `failed=False`, `nodeid="test_x.py::test_ok"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports` has one entry with `status="passed"` and `name="test_x.py::test_ok"`

#### Scenario: logreport creates failed report with message

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin with a mock report having `when="call"`, `passed=False`, `failed=True`, `longrepr="assert False"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports[0].status == "failed"` and `plugin.reports[0].message == "assert False"`

#### Scenario: logreport ignores non-call phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin with a mock report having `when="setup"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports` is empty

#### Scenario: logreport creates error report for non-passed non-failed

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin with a mock report having `when="call"`, `passed=False`, `failed=False`, `longrepr="RuntimeError: boom"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports[0].status == "error"`

### Requirement: _HarnessCollectorPlugin _append_jsonl writes valid JSON

`_append_jsonl` SHALL append a single JSON line to the output file containing
all `TestReport` fields plus an ISO-format `timestamp`. Multiple calls SHALL
produce multiple lines.

#### Scenario: _append_jsonl writes valid JSON line with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a plugin with a writable output path and a `TestReport(name="test_a", status="passed", duration_s=0.1, message="")`
- **When** `_append_jsonl` is called
- **Then** the output file contains one JSON line with keys `name`, `status`, `duration_s`, `message`, `timestamp`; `name == "test_a"` and `status == "passed"`
