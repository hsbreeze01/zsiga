# runner-coverage-gaps

## ADDED Requirements

### Requirement: TestReport dataclass construction

`TestReport` SHALL accept `name`, `status`, `duration_s`, and `message` fields and store them as
attributes.  The `__test__` class attribute SHALL be `False` so that pytest does not attempt to
collect the class itself as a test.

#### Scenario: construct TestReport with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** no preconditions
- **When** a `TestReport` is created with `name="t::a"`, `status="passed"`, `duration_s=0.5`, `message=""`
- **Then** the resulting object has `.name == "t::a"`, `.status == "passed"`, `.duration_s == 0.5`, `.message == ""`

#### Scenario: TestReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** no preconditions
- **When** the `TestReport` class is inspected
- **Then** `TestReport.__test__` is `False`

---

### Requirement: QualificationReport dataclass construction

`QualificationReport` SHALL accept `capability_results`, `regression_results`, and `passed` fields.
The `passed` field is a boolean that is `True` only when every `TestReport` across both result
lists has `status == "passed"`.

#### Scenario: QualificationReport with all-passing results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** two `TestReport` objects with `status="passed"`
- **When** a `QualificationReport` is created with those results and `passed=True`
- **Then** `.capability_results` and `.regression_results` each contain one item, and `.passed` is `True`

#### Scenario: QualificationReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** no preconditions
- **When** the `QualificationReport` class is inspected
- **Then** `QualificationReport.__test__` is `False`

---

### Requirement: _HarnessCollectorPlugin._append_jsonl writes valid JSONL

The `_append_jsonl` method SHALL append one JSON line per `TestReport` to the configured output
file.  Each line SHALL contain keys `name`, `status`, `duration_s`, `message`, and `timestamp`.

#### Scenario: _append_jsonl writes one JSON line

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file
- **When** `_append_jsonl` is called with a `TestReport(name="a::b", status="passed", duration_s=1.0, message="")`
- **Then** the output file contains exactly one line that is valid JSON with keys `name`, `status`, `duration_s`, `message`, and `timestamp`; `name` equals `"a::b"`

#### Scenario: _append_jsonl appends multiple lines

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temporary file
- **When** `_append_jsonl` is called twice with two different `TestReport` objects
- **Then** the output file contains exactly two lines, each valid JSON

---

### Requirement: _HarnessCollectorPlugin.pytest_runtest_logreport filters non-call phase

The `pytest_runtest_logreport` method SHALL ignore reports where `report.when != "call"` and only
create `TestReport` entries for the `"call"` phase.

#### Scenario: non-call report is ignored

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report having `when="setup"` and `passed=True`
- **Then** `plugin.reports` is empty and no JSONL line is written

---

### Requirement: _HarnessCollectorPlugin.pytest_runtest_logreport records failed test

When a report with `when="call"` and `failed=True` is received, the plugin SHALL create a
`TestReport` with `status="failed"` and `message` set to the string representation of
`report.longrepr`.

#### Scenario: failed call report recorded

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report having `when="call"`, `failed=True`, `passed=False`, `duration=0.3`, `nodeid="test_x::test_a"`, and `longrepr="AssertionError"`
- **Then** `plugin.reports` contains one `TestReport` with `status="failed"` and `message="AssertionError"`

---

### Requirement: _HarnessCollectorPlugin.pytest_runtest_logreport records error test

When a report with `when="call"` is neither passed nor failed (i.e., an error/skipped outcome),
the plugin SHALL create a `TestReport` with `status="error"`.

#### Scenario: error call report recorded

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report having `when="call"`, `passed=False`, `failed=False`, `duration=0.1`, `nodeid="test_y::test_b"`, and `longrepr=""`
- **Then** `plugin.reports` contains one `TestReport` with `status="error"`

---

### Requirement: HarnessRunner._run_file handles unloadable module gracefully

When `importlib.util.spec_from_file_location` returns `None` or a spec with `loader=None`, the
`_run_file` method SHALL append a `TestError` event and increment `errors`, without raising an
exception.

#### Scenario: spec is None produces TestError

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` with an initialized `_result`
- **When** `_run_file` is called with a `Path` that cannot produce a valid import spec (e.g., an empty file with `.py` extension in a non-existent directory tree)
- **Then** `runner.results.errors` is incremented and a `TestError` event is appended with a non-empty `error_message`

---

### Requirement: HarnessRunner.__init__ accepts optional fixtures

The `HarnessRunner` constructor SHALL accept an optional `fixtures` list and store it internally.
When `fixtures` is `None`, an empty list SHALL be used as default.

#### Scenario: init with explicit fixtures

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** no preconditions
- **When** `HarnessRunner(fixtures=["a", "b"])` is called
- **Then** the runner's internal `_fixtures` attribute equals `["a", "b"]`

#### Scenario: init with no fixtures defaults to empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** no preconditions
- **When** `HarnessRunner()` is called with no arguments
- **Then** the runner's internal `_fixtures` attribute is `[]`

---

### Requirement: _HarnessCollectorPlugin.pytest_runtest_logstart records start time

The `pytest_runtest_logstart` method SHALL record the start time for the given `nodeid` in the
internal `_start_times` dictionary.

#### Scenario: logstart records start time

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart` is called with `nodeid="test_foo::test_bar"`
- **Then** `plugin._start_times["test_foo::test_bar"]` is a positive float

---

### Requirement: _HarnessCollectorPlugin.pytest_collection_modifyitems is no-op

The `pytest_collection_modifyitems` hook SHALL be a no-op (accept any arguments without error).

#### Scenario: collection modifyitems does not raise

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_collection_modifyitems
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_collection_modifyitems` is called with arbitrary arguments
- **Then** no exception is raised
