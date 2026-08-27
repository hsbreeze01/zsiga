# Spec: Runner Coverage Gap Supplement

> Supplements `tests/test_harness_runner.py` with tests for uncovered classes and methods
> in `zsiga/harness/runner.py`. Does NOT create a new test file.

## MODIFIED Requirements

### Requirement: TestReport dataclass coverage

The test suite SHALL include tests verifying `TestReport` construction, field defaults,
and the `__test__ = False` attribute that prevents pytest from collecting it as a test class.

#### Scenario: TestReport default construction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::TestReport
- **Given** a newly constructed `TestReport(name="t1", status="passed", duration_s=0.1, message="")`
- **When** all fields are accessed
- **Then** `name` equals `"t1"`, `status` equals `"passed"`, `duration_s` equals `0.1`, `message` equals `""`

#### Scenario: TestReport __test__ attribute is False

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::TestReport
- **Given** the `TestReport` class
- **When** `TestReport.__test__` is accessed
- **Then** it equals `False`

#### Scenario: TestReport status field accepts valid values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::TestReport
- **Given** three `TestReport` instances with `status="passed"`, `status="failed"`, and `status="error"` respectively
- **When** each `status` field is inspected
- **Then** each instance retains its respective status string

### Requirement: QualificationReport dataclass coverage

The test suite SHALL include tests verifying `QualificationReport` construction, its
`passed` field semantics (True only if ALL contained reports have status "passed"),
and the `__test__ = False` attribute.

#### Scenario: QualificationReport with all passing reports

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` with `capability_results` containing one `TestReport(status="passed")`
  and `regression_results` containing one `TestReport(status="passed")`, and `passed=True`
- **When** the `passed` field is accessed
- **Then** it equals `True`

#### Scenario: QualificationReport with mixed results

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` with one passed and one failed report, and `passed=False`
- **When** the `passed` field is accessed
- **Then** it equals `False`

#### Scenario: QualificationReport __test__ attribute is False

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** the `QualificationReport` class
- **When** `QualificationReport.__test__` is accessed
- **Then** it equals `False`

#### Scenario: QualificationReport with empty result lists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::QualificationReport
- **Given** a `QualificationReport` with empty `capability_results` and `regression_results`, and `passed=True`
- **When** all fields are inspected
- **Then** `capability_results` is `[]`, `regression_results` is `[]`, and `passed` is `True`

### Requirement: HarnessRunner.run_pytest() coverage

The test suite SHALL include tests verifying `run_pytest()` executes pytest and returns
a list of `TestReport` objects.

#### Scenario: run_pytest on a passing test file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_ok.py` with `def test_ok(): assert True`,
  and a `HarnessRunner` instance
- **When** `runner.run_pytest([str(test_file)])` is called
- **Then** the returned list contains at least one `TestReport` whose `status` is `"passed"`

#### Scenario: run_pytest on a failing test file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_fail.py` with `def test_fail(): assert False`,
  and a `HarnessRunner` instance
- **When** `runner.run_pytest([str(test_file)])` is called
- **Then** the returned list contains at least one `TestReport` whose `status` is `"failed"`

### Requirement: _HarnessCollectorPlugin coverage

The test suite SHALL include tests verifying `_HarnessCollectorPlugin` collects reports
and writes JSONL output during pytest execution.

#### Scenario: plugin writes JSONL output file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing a passing test file and an output path for JSONL
- **When** `runner.run_pytest([str(test_file)], output_path=str(output_jsonl))` is called
- **Then** the output JSONL file exists and contains at least one valid JSON line with a `"status"` key

#### Scenario: plugin collects multiple reports from multiple tests

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary test file containing 2 passing test functions, and a `HarnessRunner` instance
- **When** `runner.run_pytest([str(test_file)])` is called
- **Then** the returned list has length 2 and all reports have `status="passed"`

### Requirement: HarnessRunner.__init__ fixtures parameter coverage

The test suite SHALL include tests verifying `HarnessRunner.__init__` accepts the `fixtures`
parameter and stores it internally.

#### Scenario: HarnessRunner constructed with fixtures

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** a `HarnessRunner` constructed with `fixtures=[{"key": "val"}]`
- **When** `runner._fixtures` is accessed
- **Then** it equals `[{"key": "val"}]`

#### Scenario: HarnessRunner constructed with None defaults to empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** a `HarnessRunner` constructed with no arguments
- **When** `runner._fixtures` is accessed
- **Then** it equals `[]`

### Requirement: _run_file module load failure edge case

The test suite SHALL include a test verifying `_run_file` gracefully handles a module
whose spec cannot be loaded (returns `None`).

#### Scenario: _run_file with unloadable module spec

- **testable**: false
- **When** `_run_file` is called with a path that causes `importlib.util.spec_from_file_location` to return `None`
- **Then** a `TestError` event is appended and `errors` is incremented
- **Note**: This scenario requires mocking `importlib.util.spec_from_file_location` which is an internal
  implementation detail. It is kept for documentation but not mechanically tested.

