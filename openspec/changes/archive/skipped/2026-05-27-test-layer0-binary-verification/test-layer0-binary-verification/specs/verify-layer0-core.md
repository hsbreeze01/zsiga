# verify-layer0-core — Layer 0 Core Data Structures and Check Functions

## ADDED Requirements

### Requirement: Layer0Check dataclass serialisation

The system SHALL provide a `Layer0Check` dataclass with fields `id`, `description`, `passed`, `evidence` and a `to_dict()` method that returns a dict with those four keys.

#### Scenario: Layer0Check round-trip via to_dict

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Check
- **Given** a `Layer0Check` instance with `id="test"`, `description="desc"`, `passed=True`, `evidence="ev"`
- **When** `to_dict()` is called
- **Then** the result is `{"id": "test", "description": "desc", "passed": True, "evidence": "ev"}`

---

### Requirement: Layer0Result aggregation

The system SHALL provide a `Layer0Result` dataclass that aggregates a list of `Layer0Check` instances and exposes `all_passed`, `failed_checks`, `passed_count`, `total_count` properties.

#### Scenario: Layer0Result with mixed pass and fail

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Result
- **Given** a `Layer0Result` containing 3 passing checks and 2 failing checks
- **When** properties are queried
- **Then** `all_passed` is `False`, `passed_count` is 3, `failed_checks` has length 2

#### Scenario: Layer0Result with all passing

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Result
- **Given** a `Layer0Result` containing only passing checks
- **When** `all_passed` is queried
- **Then** it returns `True`

---

### Requirement: spec_file_coverage check

The system SHALL provide `check_spec_file_coverage` that verifies every spec file in `specs/` has at least one corresponding keyword match in the git diff. When no spec files exist, it SHALL return passed with skip evidence.

#### Scenario: spec_file_coverage passes with matching keywords

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change directory with one spec file whose keywords match a changed file in the diff
- **When** `check_spec_file_coverage` runs
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: spec_file_coverage fails when no keywords match

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change directory with spec files whose keywords have no match in the diff
- **When** `check_spec_file_coverage` runs
- **Then** the returned `Layer0Check` has `passed=False` and evidence lists uncovered specs

#### Scenario: spec_file_coverage skips when no spec files

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change directory with no `specs/` subdirectory or empty specs
- **When** `check_spec_file_coverage` runs
- **Then** the returned `Layer0Check` has `passed=True`

---

### Requirement: tasks_completion check

The system SHALL provide `check_tasks_completion` that verifies all task items in `tasks.md` are checked off. When no `tasks.md` exists or it is empty, it SHALL return passed with skip evidence.

#### Scenario: tasks_completion passes with all checked items

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a `tasks.md` with all items as `- [x]`
- **When** `check_tasks_completion` runs
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: tasks_completion fails with unchecked items

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a `tasks.md` containing `- [ ]` unchecked items
- **When** `check_tasks_completion` runs
- **Then** the returned `Layer0Check` has `passed=False` and evidence mentions the count of unchecked items

#### Scenario: tasks_completion skips with no tasks file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a change directory with no `tasks.md`
- **When** `check_tasks_completion` runs
- **Then** the returned `Layer0Check` has `passed=True`

---

### Requirement: testable_not_all_false check

The system SHALL provide `check_testable_not_all_false` that verifies at least one scenario across all spec files is marked `testable=true`. When no specs or no scenarios exist, it SHALL return passed with skip evidence.

#### Scenario: testable_not_all_false passes with at least one testable scenario

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_testable_not_all_false
- **Given** a spec file containing at least one scenario with `testable: true`
- **When** `check_testable_not_all_false` runs
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: testable_not_all_false fails when all scenarios are not testable

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_testable_not_all_false
- **Given** spec files where every scenario has `testable: false` or no testable field
- **When** `check_testable_not_all_false` runs
- **Then** the returned `Layer0Check` has `passed=False`

---

### Requirement: no_syntax_error check

The system SHALL provide `check_no_syntax_error` that compile-checks all changed Python files. When no Python files changed, it SHALL return passed with skip evidence.

#### Scenario: no_syntax_error passes with valid Python

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_no_syntax_error
- **Given** changed Python files that are syntactically valid
- **When** `check_no_syntax_error` runs
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: no_syntax_error fails with syntax error

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_no_syntax_error
- **Given** a changed Python file with a syntax error
- **When** `check_no_syntax_error` runs
- **Then** the returned `Layer0Check` has `passed=False`

---

### Requirement: spec_scenario_coverage check

The system SHALL provide `check_spec_scenario_coverage` that extracts key SHALL/MUST terms from each spec and verifies a sufficient fraction appear in the git diff.

#### Scenario: spec_scenario_coverage passes with matching terms

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_scenario_coverage
- **Given** a spec containing `SHALL provide phase_cap` and a diff containing `phase_cap`
- **When** `check_spec_scenario_coverage` runs
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: spec_scenario_coverage fails when key terms missing from diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_scenario_coverage
- **Given** a spec with key terms that do not appear in the diff
- **When** `check_spec_scenario_coverage` runs
- **Then** the returned `Layer0Check` has `passed=False`

---

### Requirement: BAC acceptance checks

The system SHALL provide `check_bac_acceptance` that parses BAC items from `proposal.md` and evaluates each using pattern matching for: symbol existence in file, term reference in file, spec coverage delegation, and testable count.

#### Scenario: BAC exists check passes when symbol is in file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md with `[BAC-01] tests/test_verify_layer0.py 中存在 test_spec_file_coverage_pass` and the file containing that symbol
- **When** `check_bac_acceptance` runs
- **Then** the returned list includes a check with `passed=True` and id `bac_01`

#### Scenario: BAC exists check fails when symbol is missing

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md with `[BAC-01] loop.py 中存在 nonexistent_symbol_xyz` and the file not containing that symbol
- **When** `check_bac_acceptance` runs
- **Then** the returned list includes a check with `passed=False`

#### Scenario: BAC reference check passes when term is in file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md with `[BAC-02] orchestrator.py 中引用了 cap_exceeded` and the file containing `cap_exceeded`
- **When** `check_bac_acceptance` runs
- **Then** the returned list includes a check with `passed=True`

#### Scenario: BAC testable count passes with sufficient testable scenarios

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md with `[BAC-10] 至少存在 1 个 testable=true` and specs with at least 1 testable=true scenario
- **When** `check_bac_acceptance` runs
- **Then** the returned list includes a check with `passed=True`

#### Scenario: BAC testable count fails with zero testable scenarios

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md with `[BAC-10] 至少存在 1 个 testable=true` and specs with 0 testable=true scenarios
- **When** `check_bac_acceptance` runs
- **Then** the returned list includes a check with `passed=False`

---

### Requirement: run_layer0_checks orchestrator

The system SHALL provide `run_layer0_checks` that executes all individual checks in sequence, persists `verify_layer0.json`, and returns a `Layer0Result`.

#### Scenario: run_layer0_checks all pass

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::run_layer0_checks
- **Given** a change directory and target where all individual checks would pass
- **When** `run_layer0_checks` runs
- **Then** the returned `Layer0Result` has `all_passed=True`

#### Scenario: run_layer0_checks with partial failure

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::run_layer0_checks
- **Given** a change directory where at least one check (e.g. spec_file_coverage) fails
- **When** `run_layer0_checks` runs
- **Then** the returned `Layer0Result` has `all_passed=False` and `failed_checks` includes the failed check id
