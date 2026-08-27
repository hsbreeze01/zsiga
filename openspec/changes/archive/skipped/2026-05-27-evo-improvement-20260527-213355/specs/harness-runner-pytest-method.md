# harness-runner-pytest-method

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest executes tests and returns TestReport list

`HarnessRunner.run_pytest(test_paths, output_path)` SHALL invoke `pytest.main()` with the given paths plus standard flags (`-p no:cacheprovider --tb=short`), collect results via `_HarnessCollectorPlugin`, and return a `list[TestReport]`.

#### Scenario: run_pytest returns list of TestReport objects

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory containing `test_pass.py` with `def test_ok(): assert True`
- **When** `HarnessRunner().run_pytest([str(test_pass_py)], output_path=str(jsonl_path))` is called
- **Then** the return value is a list containing at least one `TestReport` whose `.name` contains `"test_ok"` and `.status == "passed"`

#### Scenario: run_pytest with failing test returns failed TestReport

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory containing `test_fail.py` with `def test_bad(): assert False`
- **When** `HarnessRunner().run_pytest([str(test_fail_py)], output_path=str(jsonl_path))` is called
- **Then** the return value contains a `TestReport` whose `.name` contains `"test_bad"` and `.status == "failed"` and `.message` is non-empty

---

### Requirement: _HarnessCollectorPlugin collects reports and writes JSONL

`_HarnessCollectorPlugin` SHALL implement pytest hooks (`pytest_runtest_logreport`) to produce `TestReport` objects. For each test's call phase, it SHALL append a JSON line to the configured `output_path` with keys `name`, `status`, `duration_s`, `message`, `timestamp`.

#### Scenario: Plugin reports list matches executed tests

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin

- **Given** a `_HarnessCollectorPlugin` instance used via `HarnessRunner().run_pytest(...)` on a temp file with one passing test
- **When** the run completes
- **Then** `plugin.reports` is a list of exactly 1 `TestReport` with `.status == "passed"`

#### Scenario: Plugin writes JSONL output file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin

- **Given** a `_HarnessCollectorPlugin` with `output_path` pointing to a temp file, used via `run_pytest` on a test file
- **When** the run completes
- **Then** the output file exists, each line is valid JSON with keys `name`, `status`, `duration_s`, `message`, `timestamp`

#### Scenario: Plugin ignores setup and teardown phases

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::_HarnessCollectorPlugin

- **Given** a `_HarnessCollectorPlugin` used via `run_pytest` on a test file with a fixture
- **When** the run completes
- **Then** `plugin.reports` contains only one entry per test function (call phase only), not one per setup/teardown

---

### Requirement: HarnessRunner.run_pytest output_path defaults to harness-results.jsonl

When `output_path` is not specified, `run_pytest` SHALL default to `"harness-results.jsonl"`.

#### Scenario: Default output_path is harness-results.jsonl

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a temporary directory with a passing test file
- **When** `HarnessRunner().run_pytest([str(test_file)])` is called without `output_path`
- **Then** the plugin inside `run_pytest` uses `"harness-results.jsonl"` as the output path (verifiable by the plugin constructor call within the method body)

