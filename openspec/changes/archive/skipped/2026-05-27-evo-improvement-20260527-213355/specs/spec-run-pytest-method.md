# spec-run-pytest-method

## ADDED Requirements

### Requirement: HarnessRunner.run_pytest argument construction

`HarnessRunner.run_pytest()` SHALL invoke `pytest.main()` with the provided test paths plus the flags `-p no:cacheprovider` and `--tb=short`. The `_HarnessCollectorPlugin` instance SHALL be passed as a plugin.

#### Scenario: run_pytest passes correct arguments to pytest.main

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a HarnessRunner instance
- **When** `run_pytest(["tests/test_foo.py"])` is called with `pytest.main` mocked
- **Then** the args list passed to `pytest.main` SHALL contain `"tests/test_foo.py"`, `"-p"`, `"no:cacheprovider"`, and `"--tb=short"`, and the plugins list SHALL contain a `_HarnessCollectorPlugin` instance

#### Scenario: run_pytest returns plugin reports

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a HarnessRunner instance with `pytest.main` mocked to be a no-op
- **When** `run_pytest(["tests/test_x.py"])` is called
- **Then** the return value SHALL be the `reports` attribute of the internal `_HarnessCollectorPlugin` (a list of `TestReport`)

#### Scenario: run_pytest uses default output_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a HarnessRunner instance with `pytest.main` mocked
- **When** `run_pytest(["tests/"])` is called without specifying `output_path`
- **Then** the `_HarnessCollectorPlugin` created SHALL have `output_path == "harness-results.jsonl"`

#### Scenario: run_pytest uses custom output_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run_pytest

- **Given** a HarnessRunner instance with `pytest.main` mocked
- **When** `run_pytest(["tests/"], output_path="/tmp/custom.jsonl")` is called
- **Then** the `_HarnessCollectorPlugin` created SHALL have `output_path == "/tmp/custom.jsonl"`

