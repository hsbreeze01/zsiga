# test-discovery-subpackage-matching

> Fix the `_scan_code_structure()` basename matching bug that causes false-positive
> "modules without tests" entries for subpackage modules whose test file follows
> the `test_{subpkg}_{module}.py` naming convention.

## MODIFIED Requirements

### Requirement: test_discovery_subpackage_match

The `_scan_code_structure()` method in `zsiga/intake/evolution.py` SHALL
recognize that a module `zsiga/{subpkg}/{module}.py` is tested when a file
`tests/test_{subpkg}_{module}.py` exists. Currently only the basename
(`module`) is matched against test file stems, so `harness/runner.py`
(basename `runner`) never matches `test_harness_runner.py` (stem
`harness_runner`).

#### Scenario: subpackage module correctly recognized as tested

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a project layout where `zsiga/harness/runner.py` exists and `tests/test_harness_runner.py` exists
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: top-level module still matched by basename

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a project layout where `zsiga/config.py` exists and `tests/test_config.py` exists
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/config.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: deeply nested subpackage module matched

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a project layout where `zsiga/pipeline/orchestrator/engine.py` exists and `tests/test_pipeline_orchestrator_engine.py` exists
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/pipeline/orchestrator/engine.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: truly untested module still reported

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a project layout where `zsiga/new_feature.py` exists and no `test_new_feature.py` or matching subpackage test exists
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/new_feature.py` SHALL appear in `modules_without_tests`

#### Scenario: module_scans not populated for correctly matched tested modules

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a project layout where `zsiga/harness/runner.py` exists with function definitions and `tests/test_harness_runner.py` exists
- **When** `_scan_code_structure()` is called
- **Then** neither `runner` nor `harness_runner` SHALL appear in `module_scans` keys
