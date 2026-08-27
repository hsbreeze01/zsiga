# runner-pytest-integration

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin end-to-end hook processing

The plugin SHALL process pytest hooks in sequence: `logstart` records start
times, `logreport` creates `TestReport` objects for call-phase results, and
non-call phases are ignored.

#### Scenario: Plugin records start time on logstart

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_file.py::test_func", None)` is called
- **Then** `plugin._start_times["test_file.py::test_func"]` is a positive float

#### Scenario: Plugin creates passed TestReport

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin and a mock report with `when="call"`, `passed=True`, `failed=False`, `nodeid="test_x.py::test_a"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports` has one `TestReport` with `status="passed"`

#### Scenario: Plugin creates failed TestReport with message

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin and a mock report with `when="call"`, `passed=False`, `failed=True`, `longrepr="AssertionError: expected 5"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports[0].status == "failed"` and `plugin.reports[0].message == "AssertionError: expected 5"`

#### Scenario: Plugin ignores setup and teardown phases

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a plugin and a mock report with `when="setup"`
- **When** `pytest_runtest_logreport` is called
- **Then** `plugin.reports == []`

### Requirement: _HarnessCollectorPlugin _append_jsonl append behavior

`_append_jsonl` SHALL write one JSON line per call, so multiple calls produce
a multi-line JSONL file where each line is independently parseable.

#### Scenario: _append_jsonl writes valid JSON line

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a plugin writing to a temp file and a `TestReport(name="t", status="passed", duration_s=0.01, message="")`
- **When** `_append_jsonl` is called
- **Then** the file has exactly one line, parseable as JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`

#### Scenario: _append_jsonl appends multiple entries

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a plugin writing to a temp file
- **When** `_append_jsonl` is called twice with different `TestReport` instances
- **Then** the file has exactly 2 lines, each independently parseable as JSON

### Requirement: HarnessRunner run_pytest returns TestReport list

`HarnessRunner.run_pytest` SHALL execute pytest via `pytest.main()` with the
provided test paths and return a list of `TestReport` objects collected by the
internal `_HarnessCollectorPlugin`.

#### Scenario: run_pytest returns list of TestReport

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary test file containing `def test_ok(): assert True`
- **When** `runner.run_pytest([str(test_file)])` is called
- **Then** the return value is a list containing at least one `TestReport`, and at least one has `status="passed"`
