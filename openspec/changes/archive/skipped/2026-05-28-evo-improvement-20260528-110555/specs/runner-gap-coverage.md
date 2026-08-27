# runner-gap-coverage

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin filters call-phase only

`_HarnessCollectorPlugin.pytest_runtest_logreport` SHALL only process reports where `report.when == "call"`. Reports with `when` of `"setup"` or `"teardown"` SHALL be silently ignored (no report appended, no JSONL line written).

For call-phase reports, status SHALL be determined as: `"passed"` when `report.passed` is `True`; `"failed"` when `report.failed` is `True`; `"error"` otherwise.

#### Scenario: call-phase passed report is processed

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance and a mock report with `when="call"`, `passed=True`, `failed=False`, `nodeid="test_file.py::test_ok"`, `duration=0.1`, `longrepr=None`
- **When** `plugin.pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` SHALL contain exactly one `TestReport` with `status="passed"`, `name="test_file.py::test_ok"`, and `duration_s > 0`

#### Scenario: call-phase failed report produces status failed

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance and a mock report with `when="call"`, `passed=False`, `failed=True`, `nodeid="test_file.py::test_bad"`, `duration=0.3`, `longrepr="AssertionError: assert False"`
- **When** `plugin.pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` SHALL contain exactly one `TestReport` with `status="failed"` and `message="AssertionError: assert False"`

#### Scenario: call-phase error report produces status error

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance and a mock report with `when="call"`, `passed=False`, `failed=False`, `nodeid="test_file.py::test_broken"`, `duration=0.05`, `longrepr="RuntimeError: crash"`
- **When** `plugin.pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` SHALL contain exactly one `TestReport` with `status="error"` and `message="RuntimeError: crash"`

#### Scenario: setup-phase report is ignored

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance and a mock report with `when="setup"`, `passed=True`, `nodeid="test_file.py::test_ok"`, `duration=0.05`, `longrepr=None`
- **When** `plugin.pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` SHALL be empty (no report appended)

#### Scenario: teardown-phase report is ignored

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance and a mock report with `when="teardown"`, `passed=True`, `nodeid="test_file.py::test_ok"`, `duration=0.02`, `longrepr=None`
- **When** `plugin.pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` SHALL be empty (no report appended)

---

### Requirement: _HarnessCollectorPlugin records start times

`_HarnessCollectorPlugin.pytest_runtest_logstart` SHALL record the start time for each test node.

#### Scenario: logstart records start time

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `plugin.pytest_runtest_logstart("test_file.py::test_ok", None)` is called
- **Then** `plugin._start_times` SHALL contain the key `"test_file.py::test_ok"` with a float value representing the current time

#### Scenario: logstart records multiple nodes

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `plugin.pytest_runtest_logstart("test_a.py::test_one", None)` and `plugin.pytest_runtest_logstart("test_b.py::test_two", None)` are called
- **Then** `plugin._start_times` SHALL contain both keys with float values

---

### Requirement: _HarnessCollectorPlugin._append_jsonl writes valid JSON lines

`_append_jsonl` SHALL append one valid JSON object per line to the output file. Each line SHALL contain keys `name`, `status`, `duration_s`, `message`, and `timestamp`. Multiple calls SHALL produce multiple lines.

#### Scenario: single JSONL append

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file, and a `TestReport(name="test_a", status="passed", duration_s=0.5, message="")`
- **When** `plugin._append_jsonl(report)` is called
- **Then** the output file SHALL contain exactly one line, which is valid JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`

#### Scenario: multiple JSONL appends accumulate

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file, and two `TestReport` objects
- **When** `_append_jsonl` is called twice with different reports
- **Then** the output file SHALL contain exactly two lines, each being valid JSON, and the second line SHALL have a different `name` than the first

---

### Requirement: _HarnessCollectorPlugin.pytest_collection_modifyitems is no-op

`pytest_collection_modifyitems` SHALL be a no-op method (does nothing, returns nothing).

#### Scenario: collection modifyitems does not raise

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_collection_modifyitems
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `plugin.pytest_collection_modifyitems(None, None)` is called
- **Then** no exception SHALL be raised and `plugin.reports` SHALL remain empty
