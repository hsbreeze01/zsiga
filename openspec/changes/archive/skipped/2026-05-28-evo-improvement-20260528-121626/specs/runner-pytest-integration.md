# runner-pytest-integration

## ADDED Requirements

### Requirement: _HarnessCollectorPlugin tracks start times

The `_HarnessCollectorPlugin` SHALL record start timestamps keyed by `nodeid`
when `pytest_runtest_logstart` is called. Each nodeid SHALL map to a `float`
timestamp.

#### Scenario: logstart records timestamp by nodeid

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a _HarnessCollectorPlugin instance with an empty `_start_times` dict
- **When** `pytest_runtest_logstart` is called with nodeid="test_a::test_one" and location=()
- **Then** `_start_times["test_a::test_one"]` SHALL be a float greater than 0

---

### Requirement: _HarnessCollectorPlugin processes only call-phase reports

When `pytest_runtest_logreport` is invoked, it SHALL ignore reports whose `when`
attribute is not `"call"`. Only call-phase reports SHALL produce a `TestReport` entry.

#### Scenario: logreport ignores setup phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a _HarnessCollectorPlugin instance with empty reports list
- **When** `pytest_runtest_logreport` is called with a mock report whose `when="setup"`, `passed=True`, `nodeid="test_x"`, `duration=0.0`, `longrepr=None`
- **Then** the `reports` list SHALL remain empty

#### Scenario: logreport ignores teardown phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a _HarnessCollectorPlugin instance with empty reports list
- **When** `pytest_runtest_logreport` is called with a mock report whose `when="teardown"`, `passed=True`, `nodeid="test_x"`, `duration=0.0`, `longrepr=None`
- **Then** the `reports` list SHALL remain empty

#### Scenario: logreport creates TestReport for passed call phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a _HarnessCollectorPlugin instance with a temporary JSONL output path
- **When** `pytest_runtest_logreport` is called with a mock report where `when="call"`, `passed=True`, `failed=False`, `nodeid="test_x::test_ok"`, `duration=0.123`, `longrepr=None`
- **Then** `reports` SHALL contain exactly one TestReport with `status="passed"`, `name="test_x::test_ok"`, and `duration_s` equal to 0.123

#### Scenario: logreport creates TestReport for failed call phase

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a _HarnessCollectorPlugin instance with a temporary JSONL output path
- **When** `pytest_runtest_logreport` is called with a mock report where `when="call"`, `passed=False`, `failed=True`, `nodeid="test_x::test_bad"`, `duration=0.05`, `longrepr="AssertionError: assert False"`
- **Then** `reports` SHALL contain exactly one TestReport with `status="failed"` and `message` containing "assert False"

---

### Requirement: _HarnessCollectorPlugin appends JSONL output

When a `TestReport` is produced during the call phase, the plugin SHALL append
one JSON line to the output file. Each line MUST contain the keys `name`, `status`,
`duration_s`, `message`, and `timestamp`. The `timestamp` field MUST be an ISO-8601
string.

#### Scenario: append_jsonl writes valid JSON line to output file

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a _HarnessCollectorPlugin with output_path pointing to a temporary file and a TestReport with name="test_a", status="passed", duration_s=0.1, message=""
- **When** `_append_jsonl` is called with that TestReport
- **Then** the output file SHALL exist, contain exactly one line, and the line SHALL parse as valid JSON with keys "name", "status", "duration_s", "message", and "timestamp"

#### Scenario: append_jsonl appends multiple lines

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a _HarnessCollectorPlugin with output_path pointing to a temporary file
- **When** `_append_jsonl` is called twice with two different TestReport instances
- **Then** the output file SHALL contain exactly two lines

---

### Requirement: HarnessRunner.run_pytest invokes pytest and returns reports

`HarnessRunner.run_pytest` SHALL accept a list of test path strings and an optional
output_path string. It MUST invoke `pytest.main` with the given paths plus standard
flags (`-p no:cacheprovider --tb=short`) and return a list of `TestReport` objects
collected by the internal plugin.

#### Scenario: run_pytest returns TestReport list for passing tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing one test file with a passing test, and a HarnessRunner instance
- **When** `run_pytest` is called with the path to that test file
- **Then** the return value SHALL be a non-empty list of TestReport objects, and at least one report SHALL have status="passed"

#### Scenario: run_pytest creates JSONL output file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing one test file with a passing test, and a HarnessRunner instance with output_path set to a temporary file path
- **When** `run_pytest` is called
- **Then** the JSONL output file SHALL exist and be non-empty
