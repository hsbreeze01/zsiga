# phase-harness-runner-pytest.md

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest returns TestReport list

`HarnessRunner.run_pytest(test_paths, output_path)` SHALL invoke `pytest.main()` with the given test paths and a `_HarnessCollectorPlugin` instance.  It MUST return the `plugin.reports` list (a list of `TestReport` objects).

#### Scenario: run_pytest with a passing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_ok.py` with `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(tmp_path / "out.jsonl"))` is called
- **Then** the returned list contains at least one `TestReport` with `.status == "passed"` and `.name` containing `"test_ok"`

#### Scenario: run_pytest with a failing test file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_fail.py` with `def test_fail(): assert False`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(tmp_path / "out.jsonl"))` is called
- **Then** the returned list contains at least one `TestReport` with `.status == "failed"`

#### Scenario: run_pytest creates JSONL output file

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** a temporary directory containing `test_ok.py` with `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_file)], output_path=str(tmp_path / "results.jsonl"))` is called
- **Then** the file `results.jsonl` exists, and each line is valid JSON containing `"name"`, `"status"`, `"duration_s"`, `"message"`, and `"timestamp"` keys

---

### Requirement: HarnessRunner.run_pytest passes correct pytest arguments

`run_pytest` SHALL construct the pytest argument list as `test_paths + ["-p", "no:cacheprovider", "--tb=short"]` plus the collector plugin.

#### Scenario: run_pytest with empty test_paths list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest
- **Given** an empty `test_paths` list
- **When** `HarnessRunner().run_pytest([], output_path=str(tmp_path / "out.jsonl"))` is called
- **Then** it returns an empty list of reports (no tests discovered)
