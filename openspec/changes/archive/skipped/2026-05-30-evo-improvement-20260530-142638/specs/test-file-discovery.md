# test-file-discovery

## MODIFIED Requirements

### Requirement: Test coverage detection MUST use import-aware matching

`EvolutionEngine._scan_code_structure()` SHALL determine whether a source module has test coverage by examining import relationships in test files, not solely by exact basename matching against `test_{basename}.py`.

A source module `zsiga/{subdir}/{module}.py` SHALL be considered "covered" (and therefore excluded from `modules_without_tests`) when ANY test file in the `tests/` directory imports symbols from that source module.

#### Scenario: Exact-name test file is still recognized

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure

- **Given** a project with source file `zsiga/sample.py` and test file `tests/test_sample.py` that contains `from zsiga.sample import hello`
- **When** `_scan_code_structure()` is invoked
- **Then** `zsiga/sample.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: Prefixed test file covers module by import

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure

- **Given** a project with source file `zsiga/harness/runner.py` and test file `tests/test_harness_runner.py` that contains `from zsiga.harness.runner import HarnessRunner`
- **When** `_scan_code_structure()` is invoked
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: Differently-named test file covers module by import

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure

- **Given** a project with source file `zsiga/duration_predictor.py` and test file `tests/test_phase_duration.py` that contains `from zsiga.duration_predictor import predict_change_duration`
- **When** `_scan_code_structure()` is invoked
- **Then** `zsiga/duration_predictor.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: Module with no test file and no importing test is listed as uncovered

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure

- **Given** a project with source file `zsiga/lonely.py` and no test file that imports from `zsiga.lonely`
- **When** `_scan_code_structure()` is invoked
- **Then** `zsiga/lonely.py` SHALL appear in `modules_without_tests`

#### Scenario: Test file without corresponding source module does not cause errors

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure

- **Given** a project with test file `tests/test_phantom.py` that imports `from zsiga.nonexistent import stuff` and no `zsiga/nonexistent.py` file
- **When** `_scan_code_structure()` is invoked
- **Then** the method SHALL complete without raising an exception and the `modules_without_tests` list SHALL NOT include any path referencing `nonexistent`
