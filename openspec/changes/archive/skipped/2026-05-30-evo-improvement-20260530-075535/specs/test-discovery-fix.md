# Test Discovery Fix — Suffix Matching for Nested Modules

## MODIFIED Requirements

### Requirement: `_scan_code_structure` SHALL recognize test files that include parent directory names

The `_scan_code_structure()` method in `zsiga/intake/evolution.py` currently
extracts only the basename of each source file (e.g. `runner` from
`zsiga/harness/runner.py`) and checks for an exact match among test file
stems (e.g. checks if `runner` is in `{"harness_runner", ...}`).  This causes
false negatives for any module whose test file includes a parent directory
prefix in its name (e.g. `test_harness_runner.py` for `harness/runner.py`).

The method SHALL be modified so that a source module is considered "tested"
when **either** of the following is true:

1. The basename exactly matches a test file stem (current behavior preserved).
2. Any test file stem **ends with** `_` + basename (suffix-parent pattern).

This preserves backward compatibility for flat-named modules (e.g. `config.py`
→ `test_config.py`) while also matching nested naming conventions (e.g.
`harness/runner.py` → `test_harness_runner.py`).

#### Scenario: Exact-match module still recognized as tested

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/config.py` and a test file `tests/test_config.py` exist
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/config.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: Suffix-match module recognized as tested (harness_runner → runner)

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/harness/runner.py` (basename `runner`) and a test file `tests/test_harness_runner.py` (stem `harness_runner`) exist
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: Multi-level nested module matched via suffix

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/intake/evolution.py` (basename `evolution`) and a test file `tests/test_intake_evolution.py` (stem `intake_evolution`) exist
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/intake/evolution.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: Truly untested module still reported as untested

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/brand_new_module.py` (basename `brand_new_module`) and no test file with stem `brand_new_module` or `*_brand_new_module`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/brand_new_module.py` SHALL appear in `modules_without_tests`

#### Scenario: No false positive from partial suffix overlap

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/tools.py` (basename `tools`) and only a test file `tests/test_more_tools.py` (stem `more_tools`, where `more_tools` ends with `_tools`)
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/tools.py` SHALL NOT appear in `modules_without_tests` (suffix match `more_tools` ends with `_tools`)

#### Scenario: Short basename does not falsely match unrelated test file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file `zsiga/api.py` (basename `api`) and only a test file `tests/test_data_api_client.py` (stem `data_api_client`, which does NOT end with `_api`)
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/api.py` SHALL appear in `modules_without_tests` (no exact or suffix match)

