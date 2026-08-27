# phase-collector-plugin.md

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin processes call-phase reports

`_HarnessCollectorPlugin.pytest_runtest_logreport` SHALL only process reports where `report.when == "call"`.  Reports from "setup" or "teardown" phases MUST be ignored.

#### Scenario: plugin ignores setup-phase report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with `output_path` set to a temp file
- **When** `pytest_runtest_logreport` is called with a mock report having `when="setup"` and `passed=True`
- **Then** `plugin.reports` is empty and no line is appended to the JSONL file

#### Scenario: plugin records call-phase passed report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with `output_path` set to a temp file
- **When** `pytest_runtest_logreport` is called with a mock report having `when="call"`, `passed=True`, `nodeid="test_foo::test_bar"`, `duration=0.5`
- **Then** `plugin.reports` contains one `TestReport` with `.status == "passed"`, `.name == "test_foo::test_bar"`, `.duration_s == 0.5`

#### Scenario: plugin records call-phase failed report with message

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with `output_path` set to a temp file
- **When** `pytest_runtest_logreport` is called with a mock report having `when="call"`, `failed=True`, `nodeid="test_x::test_y"`, `longrepr="AssertionError"`
- **Then** the report has `.status == "failed"` and `.message == "AssertionError"`

---

### Requirement: _HarnessCollectorPlugin JSONL output format

Each appended JSONL line SHALL be a valid JSON object with keys `name`, `status`, `duration_s`, `message`, and `timestamp`.  The `timestamp` value SHALL be an ISO-8601 string in UTC.

#### Scenario: JSONL line has required keys

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temp file
- **When** `_append_jsonl` is called with a `TestReport(name="a::b", status="passed", duration_s=0.1, message="")`
- **Then** the written line parses as JSON and contains all five keys: `name`, `status`, `duration_s`, `message`, `timestamp`

---

### Requirement: _HarnessCollectorPlugin records start times

`pytest_runtest_logstart` SHALL store the current time keyed by `nodeid` in the internal `_start_times` dict.

#### Scenario: logstart records start time for nodeid

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_a::test_b", None)` is called
- **Then** `plugin._start_times["test_a::test_b"]` is a positive float (epoch seconds)
