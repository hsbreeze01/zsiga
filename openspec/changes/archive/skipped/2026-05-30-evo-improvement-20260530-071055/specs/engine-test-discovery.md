# engine-test-discovery

The evolution engine's `_scan_code_structure()` method in
`zsiga/intake/evolution.py` SHALL correctly discover test files that use
compound naming conventions (`test_{parent}_{basename}.py`) so that modules
with nested paths (e.g., `zsiga/harness/runner.py`) are not falsely reported
as "modules without tests".

## MODIFIED Requirements

### Requirement: compound-test-name-matching

When the engine scans `tests/` for existing test coverage, it MUST match test
files to source modules using both the basename **and** the compound
`{parent}_{basename}` pattern. A module at `zsiga/harness/runner.py` (basename
`runner`) SHALL be considered covered if either `test_runner.py` or
`test_harness_runner.py` exists in `tests/`.

#### Scenario: basename-match-detects-coverage

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionIntake._scan_code_structure
- **Given** a source module at `zsiga/harness/runner.py` (basename `runner`)
- **And** a test file `tests/test_runner.py` exists
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: compound-name-match-detects-coverage

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionIntake._scan_code_structure
- **Given** a source module at `zsiga/harness/runner.py` (basename `runner`, parent dir `harness`)
- **And** a test file `tests/test_harness_runner.py` exists (but `tests/test_runner.py` does NOT)
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in `modules_without_tests`

#### Scenario: no-test-file-keeps-module-uncovered

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionIntake._scan_code_structure
- **Given** a source module at `zsiga/harness/runner.py` (basename `runner`)
- **And** neither `tests/test_runner.py` nor `tests/test_harness_runner.py` exists
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/harness/runner.py` SHALL appear in `modules_without_tests`

#### Scenario: deeply-nested-module-coverage

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionIntake._scan_code_structure
- **Given** a source module at `zsiga/intake/evolution.py` (basename `evolution`, parent dir `intake`)
- **And** a test file `tests/test_evolution.py` exists
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/intake/evolution.py` SHALL NOT appear in `modules_without_tests`
