# collector-plugin-coverage

Extends `tests/test_harness_runner.py` with tests for the previously untested
`_HarnessCollectorPlugin` internal pytest plugin.

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin collects call-phase reports

`_HarnessCollectorPlugin.pytest_runtest_logreport` SHALL ignore non-call
phases (`setup`, `teardown`) and only create `TestReport` objects for the
`when == "call"` phase.

#### Scenario: logreport ignores setup phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a mock report where `when == "setup"` and `passed == True`
- **When** `pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` is an empty list

#### Scenario: logreport records passed test

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a mock report where `when == "call"`, `passed == True`, `nodeid == "test_foo::test_ok"`, `duration == 0.05`
- **When** `pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports` contains exactly one `TestReport` with `status == "passed"` and `name == "test_foo::test_ok"`

#### Scenario: logreport records failed test with message

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a mock report where `when == "call"`, `failed == True`, `longrepr == "AssertionError: wrong"`, `nodeid == "test_bar::test_bad"`
- **When** `pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports[0].status == "failed"` and `plugin.reports[0].message == "AssertionError: wrong"`

#### Scenario: logreport records error test when not passed and not failed

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a mock report where `when == "call"`, `passed == False`, `failed == False`, `longrepr == "RuntimeError"`
- **When** `pytest_runtest_logreport(report)` is called
- **Then** `plugin.reports[0].status == "error"`

### Requirement: _HarnessCollectorPlugin records start times

`_HarnessCollectorPlugin.pytest_runtest_logstart` SHALL record the start
timestamp for a given `nodeid` in its internal `_start_times` dict.

#### Scenario: logstart records timestamp for nodeid

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_foo::test_bar", location)` is called
- **Then** `plugin._start_times` contains key `"test_foo::test_bar"` with a `float` value greater than 0

### Requirement: _HarnessCollectorPlugin appends JSONL output

`_HarnessCollectorPlugin._append_jsonl` SHALL write one valid JSON line per
call, containing `name`, `status`, `duration_s`, `message`, and `timestamp`
fields, appended to the configured output file.

#### Scenario: _append_jsonl writes valid JSONL line

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file, and a `TestReport(name="t1", status="passed", duration_s=0.1, message="")`
- **When** `_append_jsonl(report)` is called
- **Then** the output file contains exactly one line that is valid JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`

#### Scenario: _append_jsonl appends multiple lines

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file, and two `TestReport` objects
- **When** `_append_jsonl` is called twice
- **Then** the output file contains exactly two lines, each valid JSON
