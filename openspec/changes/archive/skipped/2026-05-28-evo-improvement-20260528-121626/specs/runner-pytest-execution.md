# runner-pytest-execution

## Context

`zsiga/harness/runner.py` defines `HarnessRunner.run_pytest()` (L202–L223) and the
internal `_HarnessCollectorPlugin` (L228–L283). These provide pytest-based test
execution that returns `TestReport` objects and emits JSONL output. Neither has
any test coverage — the existing `tests/test_harness_runner.py` only tests the
older `discover()/run()` path.

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest returns TestReport list

`run_pytest(test_paths, output_path)` SHALL invoke `pytest.main()` with the given
test paths and a `_HarnessCollectorPlugin`. It SHALL return the list of `TestReport`
objects collected by the plugin (one per test item in the "call" phase).

#### Scenario: run_pytest on a passing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a file `test_ok.py` with `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(jsonl_path))` is called
- **Then** the returned list contains at least one `TestReport` and at least one report has `status == "passed"`

#### Scenario: run_pytest on a failing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a file `test_fail.py` with `def test_fail(): assert False`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(jsonl_path))` is called
- **Then** the returned list contains at least one `TestReport` with `status == "failed"` and `message != ""`

---

### Requirement: _HarnessCollectorPlugin records test results

The plugin SHALL record a `TestReport` for each test item during the pytest "call"
phase. Reports for "setup" and "teardown" phases SHALL be ignored.

#### Scenario: plugin records only call-phase reports

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin
- **Given** a `_HarnessCollectorPlugin` instance with an output_path in a temp directory
- **When** `pytest_runtest_logreport` is called with a mock report where `report.when == "call"` and `report.passed is True`
- **Then** `plugin.reports` contains one `TestReport` with `status == "passed"`

#### Scenario: plugin ignores setup-phase reports

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin
- **Given** a `_HarnessCollectorPlugin` instance with an output_path in a temp directory
- **When** `pytest_runtest_logreport` is called with a mock report where `report.when == "setup"`
- **Then** `plugin.reports` is empty

---

### Requirement: _HarnessCollectorPlugin JSONL output

The plugin SHALL append one JSON line per `TestReport` to the output file. Each line
MUST be valid JSON containing `name`, `status`, `duration_s`, `message`, and
`timestamp` keys.

#### Scenario: JSONL file contains one line per report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temp file
- **When** a `TestReport(name="t::a", status="passed", duration_s=0.5, message="")` is appended
- **Then** the output file contains exactly one line, and parsing it as JSON yields `{"name": "t::a", "status": "passed", "duration_s": 0.5, "message": "", "timestamp": "<iso8601>"}`

---

### Requirement: HarnessRunner init accepts fixtures

`HarnessRunner.__init__` SHALL accept an optional `fixtures` parameter (list or None).
When `None` is passed, `_fixtures` SHALL default to an empty list.

#### Scenario: HarnessRunner with explicit fixtures

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** the `HarnessRunner` class
- **When** `HarnessRunner(fixtures=["a", "b"])` is constructed
- **Then** `runner._fixtures == ["a", "b"]`

#### Scenario: HarnessRunner with None fixtures defaults to empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** the `HarnessRunner` class
- **When** `HarnessRunner(fixtures=None)` is constructed
- **Then** `runner._fixtures == []`
