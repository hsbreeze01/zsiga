# _HarnessCollectorPlugin Hook Coverage

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin logstart hook

`_HarnessCollectorPlugin.pytest_runtest_logstart(nodeid, location)` SHALL
record the current time keyed by `nodeid` in `self._start_times`.

#### Scenario: logstart records start time

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart

- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_file.py::test_func", None)` is called
- **Then** `plugin._start_times["test_file.py::test_func"]` SHALL be a positive float

---

### Requirement: _HarnessCollectorPlugin logreport filtering

`pytest_runtest_logreport` SHALL ignore reports where `report.when != "call"`
(setup and teardown phases). For call-phase reports it SHALL derive status:
`report.passed` → `"passed"`, `report.failed` → `"failed"`, else → `"error"`.

For non-passing reports, `message` SHALL be `str(report.longrepr)` if truthy, else `""`.

#### Scenario: Plugin ignores setup-phase report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a plugin instance and a mock report with `when="setup"`, `passed=True`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports` SHALL be empty

#### Scenario: Plugin ignores teardown-phase report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a plugin instance and a mock report with `when="teardown"`, `passed=True`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports` SHALL be empty

#### Scenario: Plugin creates passed TestReport for call phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a plugin instance and a mock report with `when="call"`, `passed=True`, `nodeid="a::b"`, `duration=0.1`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports` SHALL contain one `TestReport` with `status="passed"` and `name="a::b"`

#### Scenario: Plugin creates failed TestReport with longrepr message

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a plugin instance and a mock report with `when="call"`, `passed=False`, `failed=True`, `longrepr="AssertionError"`
- **When** `pytest_runtest_logreport` is called
- **Then** the report `status` SHALL be `"failed"` and `message` SHALL be `"AssertionError"`

#### Scenario: Plugin creates error TestReport for non-passed non-failed

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a plugin instance and a mock report with `when="call"`, `passed=False`, `failed=False`, `longrepr="RuntimeError"`
- **When** `pytest_runtest_logreport` is called
- **Then** the report `status` SHALL be `"error"`

#### Scenario: Plugin uses empty message when longrepr is falsy

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a plugin instance and a mock report with `when="call"`, `passed=False`, `failed=True`, `longrepr=None`
- **When** `pytest_runtest_logreport` is called
- **Then** the report `message` SHALL be `""`

---

### Requirement: _HarnessCollectorPlugin JSONL output

`_append_jsonl(report)` SHALL append one line to `self.output_path` containing
a JSON object with keys `name`, `status`, `duration_s`, `message`, `timestamp`.
The `timestamp` SHALL be an ISO 8601 UTC string. Multiple calls SHALL produce
multiple lines.

#### Scenario: _append_jsonl writes valid JSON line

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl

- **Given** a plugin with a temporary output path
- **When** `_append_jsonl` is called with `TestReport(name="t", status="passed", duration_s=1.0, message="")`
- **Then** the output file SHALL contain one line of valid JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`
- **And** `name` SHALL equal `"t"` and `status` SHALL equal `"passed"`

#### Scenario: _append_jsonl accumulates multiple lines

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl

- **Given** a plugin with a temporary output path
- **When** `_append_jsonl` is called twice with different reports
- **Then** the output file SHALL contain exactly two lines, each valid JSON
