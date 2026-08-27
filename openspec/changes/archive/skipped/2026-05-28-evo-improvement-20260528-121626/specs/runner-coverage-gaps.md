# runner-coverage-gaps

> Context: `zsiga/harness/runner.py` is partially tested by `tests/test_harness_runner.py`
> (227 lines, 16 test functions). This spec addresses the **uncovered** public APIs:
> `TestReport`, `QualificationReport`, `HarnessRunner.run_pytest()`, and
> `_HarnessCollectorPlugin` integration.

## ADDED Requirements

### Requirement: TestReport dataclass structure

`TestReport` SHALL be a dataclass with fields `name: str`, `status: str`,
`duration_s: float`, `message: str`. It SHALL have `__test__ = False` to prevent
pytest from collecting it as a test class.

#### Scenario: TestReport fields are accessible

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a `TestReport` instance constructed with explicit field values
- **When** each field is accessed
- **Then** the values match what was passed to the constructor

#### Scenario: TestReport has __test__ = False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` class
- **When** `TestReport.__test__` is accessed
- **Then** it equals `False`

---

### Requirement: QualificationReport dataclass and passed semantics

`QualificationReport` SHALL be a dataclass with fields
`capability_results: list[TestReport]`, `regression_results: list[TestReport]`,
`passed: bool`. The `passed` field is set by the caller — it is `True` only when
**all** `TestReport` entries across both lists have `status == "passed"`.

#### Scenario: QualificationReport with all-passed reports

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` with `capability_results` and `regression_results`
  all having `status="passed"`, and `passed=True`
- **When** the `passed` field is read
- **Then** it is `True`

#### Scenario: QualificationReport with a failed report

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` where at least one `TestReport` has
  `status="failed"`, and `passed=False`
- **When** the `passed` field is read
- **Then** it is `False`

#### Scenario: QualificationReport has __test__ = False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** the `QualificationReport` class
- **When** `QualificationReport.__test__` is accessed
- **Then** it equals `False`

---

### Requirement: HarnessRunner.run_pytest returns TestReport list

`HarnessRunner.run_pytest(test_paths, output_path)` SHALL invoke `pytest.main()`
with the given paths and return a `list[TestReport]`. Each report SHALL correspond
to one test item executed by pytest. The `output_path` parameter controls where
JSONL event data is written.

#### Scenario: run_pytest with a passing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_ok.py` with `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(jsonl_path))` is called
- **Then** the returned list contains at least one `TestReport` with `status == "passed"`

#### Scenario: run_pytest with a failing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_fail.py` with `def test_fail(): assert False`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(jsonl_path))` is called
- **Then** the returned list contains at least one `TestReport` with `status == "failed"`

#### Scenario: run_pytest writes JSONL output file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a test file and a JSONL output path
- **When** `run_pytest` is called and completes
- **Then** the JSONL file exists and each line is valid JSON with keys
  `name`, `status`, `duration_s`, `message`, `timestamp`

---

### Requirement: _HarnessCollectorPlugin collects reports

`_HarnessCollectorPlugin` SHALL implement pytest hooks that collect `TestReport`
objects. It SHALL record start times on `pytest_runtest_logstart`, produce
`TestReport` instances on `pytest_runtest_logreport` (call phase only), and
append each report as a JSON line via `_append_jsonl`.

#### Scenario: plugin pytest_runtest_logreport produces correct report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report object
  having `when="call"`, `passed=True`, `nodeid="test_foo::test_bar"`,
  `duration=0.5`, `longrepr=None`
- **Then** the plugin's `reports` list contains one `TestReport` with
  `name="test_foo::test_bar"`, `status="passed"`, `duration_s=0.5`

#### Scenario: plugin ignores setup and teardown phases

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with a mock report having
  `when="setup"`
- **Then** the plugin's `reports` list is empty

#### Scenario: _append_jsonl writes valid JSON line

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a
  temporary file, and a `TestReport` instance
- **When** `_append_jsonl` is called with the report
- **Then** the output file contains one line that is valid JSON with keys
  `name`, `status`, `duration_s`, `message`, `timestamp`

---

### Requirement: HarnessRunner init accepts fixtures parameter

`HarnessRunner.__init__` SHALL accept an optional `fixtures` parameter
(`list[Any] | None`). When `None`, it SHALL default to an empty list.

#### Scenario: HarnessRunner init with default fixtures

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** a `HarnessRunner` constructed with no arguments
- **When** `run()` is called on an empty discovered directory
- **Then** it succeeds without error (fixtures default is `[]`)

#### Scenario: HarnessRunner init with explicit fixtures list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** a `HarnessRunner` constructed with `fixtures=[1, 2, 3]`
- **When** the runner is used normally
- **Then** it does not raise an error related to the fixtures parameter
