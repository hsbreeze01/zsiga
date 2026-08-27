# test-file-discovery-matching

> Fixes the root cause of 27+ false "missing tests" proposals: the exact basename
> match in `_scan_code_structure()` fails to recognize that `test_harness_runner.py`
> covers `runner.py`. The matching logic SHALL use substring containment instead of
> exact equality.

## MODIFIED Requirements

### Requirement: Test-file-to-module matching uses substring containment

`EvolutionEngine._scan_code_structure()` SHALL recognize a source module as tested
when **any** test file's extracted module name **contains** the source module's
basename as a substring, or the source module's basename **contains** the test
file's extracted module name as a substring.

This replaces the current exact-equality check (`basename in test_files` set
membership) which fails for pairs like `runner.py` ↔ `test_harness_runner.py`.

#### Scenario: Prefixed test file covers module

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/harness/runner.py` and a test file `tests/test_harness_runner.py`
- **When** `_scan_code_structure()` runs
- **Then** `runner` SHALL NOT appear in `modules_without_tests`

#### Scenario: Exact match still works

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/config.py` and a test file `tests/test_config.py`
- **When** `_scan_code_structure()` runs
- **Then** `config` SHALL NOT appear in `modules_without_tests`

#### Scenario: Unrelated modules still reported untested

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/new_feature.py` and no matching test file
- **When** `_scan_code_structure()` runs
- **Then** `zsiga/new_feature.py` SHALL appear in `modules_without_tests`

#### Scenario: Subdirectory module matched by test file

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/transport.py` and a test file `tests/test_transport.py`
- **When** `_scan_code_structure()` runs
- **Then** `transport` SHALL NOT appear in `modules_without_tests`

#### Scenario: No false cross-match between unrelated names

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/util.py` and a test file `tests/test_mutual.py` (where `"util"` is NOT a substring of `"mutual"`)
- **When** `_scan_code_structure()` runs
- **Then** `zsiga/util.py` SHALL appear in `modules_without_tests`
