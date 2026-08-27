# spec-collector-plugin

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin.pytest_runtest_logstart records start time

The plugin SHALL record the start time of each test node in an internal `_start_times` dict keyed by `nodeid`.

#### Scenario: logstart records nodeid with timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart

- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart("test_mod::test_func", None)` is called
- **Then** `plugin._start_times["test_mod::test_func"]` SHALL be a float approximately equal to `time.time()`

---

### Requirement: _HarnessCollectorPlugin.pytest_runtest_logreport processes call-phase reports

The plugin SHALL only process reports where `report.when == "call"`. For each such report it SHALL create a `TestReport` and append it to `self.reports`. The status mapping SHALL be:
- `report.passed == True` → `status="passed"`, `message=""`
- `report.failed == True` → `status="failed"`, `message=str(report.longrepr)` or `""` if `longrepr` is falsy
- otherwise → `status="error"`, `message=str(report.longrepr)` or `""` if `longrepr` is falsy

Reports with `report.when != "call"` (e.g., `"setup"`, `"teardown"`) SHALL be silently ignored.

#### Scenario: logreport with passed call report

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` and a mock report with `when="call"`, `passed=True`, `failed=False`, `duration=0.5`, `nodeid="test_a::test_ok"`, `longrepr=None`
- **When** `pytest_runtest_logreport(mock_report)` is called
- **Then** `plugin.reports` SHALL have length 1, with `status="passed"`, `name="test_a::test_ok"`, `message=""`, `duration_s` approximately 0.5

#### Scenario: logreport with failed call report

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` and a mock report with `when="call"`, `passed=False`, `failed=True`, `duration=1.2`, `nodeid="test_b::test_fail"`, `longrepr="AssertionError"`
- **When** `pytest_runtest_logreport(mock_report)` is called
- **Then** `plugin.reports[0].status == "failed"` and `message == "AssertionError"`

#### Scenario: logreport with error (skipped/xfail) report

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` and a mock report with `when="call"`, `passed=False`, `failed=False`, `duration=0.0`, `nodeid="test_c::test_err"`, `longrepr="RuntimeError"`
- **When** `pytest_runtest_logreport(mock_report)` is called
- **Then** `plugin.reports[0].status == "error"` and `message == "RuntimeError"`

#### Scenario: logreport ignores setup-phase report

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport

- **Given** a `_HarnessCollectorPlugin` and a mock report with `when="setup"`, `passed=True`
- **When** `pytest_runtest_logreport(mock_report)` is called
- **Then** `plugin.reports` SHALL be empty

---

### Requirement: _HarnessCollectorPlugin._append_jsonl writes valid JSON lines

Each call to `_append_jsonl` SHALL append exactly one line to the output file. The line SHALL be valid JSON with keys: `name`, `status`, `duration_s`, `message`, `timestamp`. The `timestamp` SHALL be an ISO-8601 string with timezone info. Multiple calls SHALL produce multi-line output without truncating previous lines.

#### Scenario: append_jsonl writes single valid JSON line

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl

- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temp file, and a `TestReport(name="t1", status="passed", duration_s=0.1, message="")`
- **When** `_append_jsonl(report)` is called
- **Then** the file SHALL contain exactly one line, which parses as JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`

#### Scenario: append_jsonl accumulates multiple reports

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl

- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temp file, and two `TestReport` instances
- **When** `_append_jsonl` is called twice
- **Then** the file SHALL contain exactly two lines, each independently parseable as valid JSON

#### Scenario: append_jsonl timestamp has timezone info

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl

- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temp file, and a `TestReport`
- **When** `_append_jsonl(report)` is called
- **Then** the parsed JSON's `timestamp` field SHALL end with `+00:00` (UTC timezone indicator)

