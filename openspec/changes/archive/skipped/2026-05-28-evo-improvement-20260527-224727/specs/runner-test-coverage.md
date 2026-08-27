# runner-test-coverage

Delta spec for adding unit tests to `zsiga/harness/runner.py`.

## Context

`zsiga/harness/runner.py` (317 lines) defines 10 classes: 5 event dataclasses
(`TestEvent`, `TestStarted`, `TestPassed`, `TestFailed`, `TestError`),
2 report dataclasses (`TestReport`, `QualificationReport`), `HarnessResult`,
`HarnessRunner`, and `_HarnessCollectorPlugin`.  An existing file
`tests/test_harness_runner.py` (17 tests) covers event dataclasses, `HarnessResult`,
`HarnessRunner.discover()`, and `HarnessRunner.run()`.

This spec adds **new test coverage** for the **untested public surface**:
`TestReport`, `QualificationReport`, `HarnessRunner.__init__` fixtures parameter,
`HarnessRunner.run_pytest()`, `HarnessRunner._run_file()` edge cases, and
`_HarnessCollectorPlugin` — in a **new file**
`tests/test_spec_evo_improvement_20260527_224727__runner_test_coverage.py`.

Source code (`zsiga/harness/runner.py`) SHALL NOT be modified.

## ADDED Requirements

### Requirement: TestReport dataclass coverage

`TestReport` is a public dataclass with fields `name`, `status`, `duration_s`,
`message`.  Tests SHALL verify construction, field access, and the `__test__`
safety guard.

#### Scenario: Construct TestReport with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` class is imported from `zsiga.harness.runner`
- **When** a `TestReport` is constructed with `name="t1"`, `status="passed"`, `duration_s=0.5`, `message=""`
- **Then** all field values match the constructor arguments: `name` is `"t1"`, `status` is `"passed"`, `duration_s` is `0.5`, `message` is `""`

#### Scenario: TestReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` class is imported
- **When** `TestReport.__test__` is accessed
- **Then** it SHALL be `False` to prevent pytest collection

---

### Requirement: QualificationReport dataclass coverage

`QualificationReport` aggregates capability and regression results with a
`passed` boolean field.  Tests SHALL verify construction with all-passed and
mixed-status results.

#### Scenario: QualificationReport all-passed

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** two `TestReport` instances both with `status="passed"`
- **When** a `QualificationReport` is constructed with `capability_results=[r1]`, `regression_results=[r2]`, `passed=True`
- **Then** `report.passed` is `True`, `report.capability_results` has length 1, and `report.regression_results` has length 1

#### Scenario: QualificationReport with failure

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** one `TestReport` with `status="failed"` and one with `status="passed"`
- **When** a `QualificationReport` is constructed with `passed=False`
- **Then** `report.passed` is `False`

#### Scenario: QualificationReport __test__ is False

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** the `QualificationReport` class is imported
- **When** `QualificationReport.__test__` is accessed
- **Then** it SHALL be `False`

---

### Requirement: HarnessRunner fixtures parameter

`HarnessRunner.__init__` accepts an optional `fixtures` list stored internally.
Tests SHALL verify both the explicit and default behaviours.

#### Scenario: HarnessRunner init with fixtures

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** the `HarnessRunner` class
- **When** constructed with `fixtures=["a", "b"]`
- **Then** `runner._fixtures` SHALL equal `["a", "b"]`

#### Scenario: HarnessRunner init without fixtures defaults to empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** the `HarnessRunner` class
- **When** constructed with no arguments
- **Then** `runner._fixtures` SHALL equal `[]`

---

### Requirement: HarnessRunner._run_file module load failure

When `_run_file` encounters a module that cannot be loaded, it SHALL emit a
`TestError` event and increment the error count.  When a valid module has no
`test_*` functions, it SHALL complete without error.

#### Scenario: _run_file handles unloadable module

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` instance and a `Path` to a `.py` file containing invalid Python syntax
- **When** `_run_file` is called with that path
- **Then** `runner.results.errors` SHALL be at least 1 and `runner.results.events` SHALL contain at least one `TestError` instance

#### Scenario: _run_file with valid module containing no test functions

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a `HarnessRunner` instance and a `Path` to a valid `.py` file with no `test_*` functions
- **When** `_run_file` is called with that path
- **Then** `runner.results.errors` SHALL be 0, `runner.results.passed` SHALL be 0, and `runner.results.failed` SHALL be 0

---

### Requirement: HarnessRunner.run_pytest() test coverage

`HarnessRunner.run_pytest()` invokes `pytest.main()` with a
`_HarnessCollectorPlugin` and returns a list of `TestReport` objects.  It SHALL
also produce a JSONL output file at the specified `output_path`.

#### Scenario: run_pytest with a passing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_ok_unit.py` with a passing `def test_ok(): assert True` function
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(jsonl_path))` is called
- **Then** the returned list SHALL contain at least one `TestReport` with `status="passed"`

#### Scenario: run_pytest writes JSONL output

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_simple_unit.py` with `def test_ok(): pass`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(jsonl_path))` is called
- **Then** the JSONL file SHALL exist and contain at least one line with `"status": "passed"`

---

### Requirement: _HarnessCollectorPlugin event collection

`_HarnessCollectorPlugin` collects `TestReport` objects via pytest hooks and
appends JSONL lines.  It SHALL only record the `"call"` phase, map
passed/failed/error statuses correctly, and write valid JSONL output.

#### Scenario: plugin collects report from pytest_runtest_logreport for passed test

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a temporary output path
- **When** `pytest_runtest_logreport` is called with a mock report object where `when="call"`, `passed=True`, `duration=0.1`, `nodeid="test_foo::test_bar"`, `longrepr=None`
- **Then** `plugin.reports` SHALL contain exactly one `TestReport` with `status="passed"` and `name="test_foo::test_bar"`

#### Scenario: plugin ignores setup and teardown phases

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logreport` is called with mock reports where `when="setup"` and `when="teardown"`
- **Then** `plugin.reports` SHALL be empty

#### Scenario: plugin records start time on logstart

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logstart
- **Given** a `_HarnessCollectorPlugin` instance
- **When** `pytest_runtest_logstart` is called with `nodeid="test_a::test_b"` and `location=None`
- **Then** `plugin._start_times` SHALL contain key `"test_a::test_b"` with a positive float value

#### Scenario: plugin handles failed test report

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a temporary output path
- **When** `pytest_runtest_logreport` is called with a mock report where `when="call"`, `failed=True`, `passed=False`, `duration=0.3`, `nodeid="test_fail::test_bad"`, `longrepr="AssertionError: boom"`
- **Then** `plugin.reports` SHALL contain one `TestReport` with `status="failed"` and `message` containing `"boom"`

#### Scenario: plugin writes valid JSONL line to output file

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin._append_jsonl
- **Given** a `_HarnessCollectorPlugin` instance with a temporary output path
- **When** `pytest_runtest_logreport` is called with a mock report for a passed call-phase test
- **Then** the output file SHALL exist and contain exactly one valid JSON line with keys `name`, `status`, `duration_s`, `message`, and `timestamp`

#### Scenario: plugin maps neither-passed-nor-failed to error status

- **testable**: true
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin.pytest_runtest_logreport
- **Given** a `_HarnessCollectorPlugin` instance with a temporary output path
- **When** `pytest_runtest_logreport` is called with a mock report where `when="call"`, `passed=False`, `failed=False`
- **Then** `plugin.reports` SHALL contain one `TestReport` with `status="error"`

---

## MODIFIED Requirements

_None — no existing specs are being changed._

## REMOVED Requirements

_None — no existing specs are being removed._

## Constraints

- SHALL create a new file `tests/test_spec_evo_improvement_20260527_224727__runner_test_coverage.py` — SHALL NOT modify `zsiga/harness/runner.py`
- SHALL NOT modify any existing test files (`tests/test_harness_runner.py`, `tests/conftest_zsiga.py`, etc.)
- All tests SHALL pass `python -m pytest tests/test_spec_evo_improvement_20260527_224727__runner_test_coverage.py` with exit code 0
- All tests SHALL pass `ruff check tests/test_spec_evo_improvement_20260527_224727__runner_test_coverage.py` with exit code 0
- The test file SHALL contain at least 14 `def test_` functions covering the requirements above
