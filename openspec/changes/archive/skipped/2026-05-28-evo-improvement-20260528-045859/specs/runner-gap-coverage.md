# runner-gap-coverage

## Summary

Supplement test coverage for `zsiga/harness/runner.py` by targeting classes and
code paths not exercised by the existing `tests/test_harness_runner.py`.

The existing test file covers event dataclasses, `HarnessResult`,
`HarnessRunner.discover()`, and `HarnessRunner.run()` happy/error paths.
The following symbols have **zero** direct test coverage:

- `TestReport` (dataclass)
- `QualificationReport` (dataclass, `passed` semantics)
- `_HarnessCollectorPlugin` (all methods: `pytest_runtest_logstart`,
  `pytest_runtest_logreport`, `pytest_collection_modifyitems`, `_append_jsonl`)
- `HarnessRunner._run_file()` — unloadable-module and exec-error branches
- `HarnessRunner.run_pytest()`
- `HarnessRunner.__init__` — `fixtures` parameter storage

## ADDED Requirements

### Requirement: TestReport dataclass construction

`TestReport` SHALL expose four fields (`name`, `status`, `duration_s`,
`message`) and act as a plain data container.

#### Scenario: construct TestReport with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a `TestReport` is instantiated with `name="t::a"`, `status="passed"`,
  `duration_s=0.123`, `message=""`
- **When** each field is read back
- **Then** all four values SHALL match the constructor arguments exactly

#### Scenario: TestReport status reflects failed outcome

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a `TestReport` with `status="failed"`
- **When** the `status` field is inspected
- **Then** it SHALL equal `"failed"`

---

### Requirement: QualificationReport dataclass and passed semantics

`QualificationReport` SHALL aggregate `capability_results` and
`regression_results` (both `list[TestReport]`) and a boolean `passed` field.
The `passed` field is a plain data attribute; its correctness is the caller's
responsibility.

#### Scenario: QualificationReport construction with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** two `TestReport` instances with `status="passed"` used as
  `capability_results` and `regression_results`
- **When** a `QualificationReport` is constructed with `passed=True`
- **Then** `report.passed` SHALL be `True`, `report.capability_results` SHALL
  have length 1, and `report.regression_results` SHALL have length 1

#### Scenario: QualificationReport with mixed results records passed as False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `TestReport(status="passed")` in `capability_results` and a
  `TestReport(status="failed")` in `regression_results`
- **When** a `QualificationReport` is constructed with `passed=False`
- **Then** `report.passed` SHALL be `False`

---

### Requirement: _HarnessCollectorPlugin tracks start times

`_HarnessCollectorPlugin.pytest_runtest_logstart` SHALL record the start
timestamp for each test node in `_start_times`.

#### Scenario: logstart records node start time

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart` is called with `nodeid="test_foo.py::test_a"`
  and `location=None`
- **Then** `plugin._start_times["test_foo.py::test_a"]` SHALL exist and be a
  positive float (epoch seconds)

#### Scenario: logstart overwrites previous entry for same nodeid

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance that already has
  `_start_times["test_foo.py::test_a"]` set to `100.0`
- **When** `pytest_runtest_logstart` is called again with the same `nodeid`
- **Then** the value SHALL be updated to a different (later) float

---

### Requirement: _HarnessCollectorPlugin processes call-phase reports only

`_HarnessCollectorPlugin.pytest_runtest_logreport` SHALL only process reports
whose `when` attribute equals `"call"`. For each call-phase report it SHALL
append a `TestReport` to `self.reports` and write a JSONL line.

#### Scenario: non-call phase report ignored

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report where
  `when="setup"`
- **Then** `plugin.reports` SHALL remain empty (length 0)

#### Scenario: teardown phase report ignored

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report where
  `when="teardown"`
- **Then** `plugin.reports` SHALL remain empty (length 0)

#### Scenario: call-phase passed report appended

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report where
  `when="call"`, `passed=True`, `nodeid="t::a"`, `duration=0.5`,
  `longrepr=None`
- **Then** `plugin.reports` SHALL contain exactly one `TestReport` with
  `status="passed"`, `duration_s=0.5`, and `name="t::a"`

#### Scenario: call-phase failed report captures longrepr

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report where
  `when="call"`, `failed=True`, `passed=False`,
  `nodeid="t::b"`, `duration=1.0`, `longrepr="assert False"`
- **Then** the appended `TestReport` SHALL have `status="failed"` and
  `message="assert False"`

#### Scenario: call-phase error report when neither passed nor failed

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report where
  `when="call"`, `passed=False`, `failed=False`,
  `nodeid="t::c"`, `duration=0.1`, `longrepr="RuntimeError"`
- **Then** the appended `TestReport` SHALL have `status="error"` and
  `message="RuntimeError"`

---

### Requirement: _HarnessCollectorPlugin writes JSONL output

`_HarnessCollectorPlugin._append_jsonl` SHALL append one JSON line containing
`name`, `status`, `duration_s`, `message`, and `timestamp` keys to the output
file.

#### Scenario: append_jsonl writes valid JSON line with correct fields

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a
  temporary file, and a `TestReport(name="x", status="passed", duration_s=0.1, message="")`
- **When** `_append_jsonl` is called with that report
- **Then** the output file SHALL contain exactly one line; parsing it as JSON
  SHALL yield a dict with keys `name`, `status`, `duration_s`, `message`,
  `timestamp` where `name=="x"`, `status=="passed"`, `duration_s==0.1`,
  `message==""`, and `timestamp` is a non-empty string

---

### Requirement: _HarnessCollectorPlugin collection hook is no-op

`_HarnessCollectorPlugin.pytest_collection_modifyitems` SHALL accept session
and items arguments without error and return `None`.

#### Scenario: collection modifyitems does not raise

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_collection_modifyitems
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_collection_modifyitems` is called with `session=None` and
  `items=None`
- **Then** no exception SHALL be raised and the return value SHALL be `None`

---

### Requirement: HarnessRunner._run_file handles unloadable modules

When `_run_file` encounters a file that cannot produce a valid module spec
(`spec_from_file_location` returns `None`), it SHALL append a `TestError`
event and increment `errors` without crashing.

#### Scenario: _run_file with null spec records error event

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with a fresh `HarnessResult`, and
  `importlib.util.spec_from_file_location` is patched to return `None`
- **When** `_run_file` is called with any `.py` path
- **Then** `result.errors` SHALL be incremented by 1, and the last event in
  `result.events` SHALL be a `TestError`

#### Scenario: _run_file with module exec exception records error event

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` and a Python file whose top-level code contains
  a syntax error (e.g. `import nonexistent_xyz_module_12345`)
- **When** `_run_file` is called with that file path
- **Then** `result.errors` SHALL be incremented by 1 and the last event SHALL
  be a `TestError` whose `error_message` is a non-empty string

---

### Requirement: HarnessRunner.__init__ stores fixtures

`HarnessRunner.__init__` SHALL accept an optional `fixtures` list and store it
internally. When no fixtures are provided, it SHALL default to an empty list.

#### Scenario: init with fixtures parameter stores the list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** `HarnessRunner(fixtures=["a", "b"])` is constructed
- **When** the internal `_fixtures` attribute is inspected
- **Then** it SHALL equal `["a", "b"]`

#### Scenario: init without fixtures defaults to empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** `HarnessRunner()` is constructed with no arguments
- **When** the internal `_fixtures` attribute is inspected
- **Then** it SHALL equal `[]`

---

### Requirement: HarnessRunner.run_pytest invokes pytest with plugin

`HarnessRunner.run_pytest` SHALL create a `_HarnessCollectorPlugin`, invoke
`pytest.main` with the given test paths and plugin, and return the plugin's
`reports` list.

#### Scenario: run_pytest returns TestReport list from passing test

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a `HarnessRunner` and a temporary test file containing a passing
  test function
- **When** `run_pytest` is called with the path to that file
- **Then** the return value SHALL be a `list` containing at least one
  `TestReport` with `status="passed"`
