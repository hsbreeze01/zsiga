# Layer 0 Binary Check Tests

## ADDED Requirements

### Requirement: Layer0Check data structure contract
Layer0Check SHALL be a dataclass with fields `id`, `description`, `passed`, `evidence`. Its `to_dict()` method SHALL return a dictionary containing all four fields.

#### Scenario: Layer0Check to_dict returns complete structure

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Check.to_dict
- **Given** a `Layer0Check` instance with `id="test_check"`, `description="A test"`, `passed=True`, `evidence="observed"`
- **When** `to_dict()` is called
- **Then** the result is `{"id": "test_check", "description": "A test", "passed": True, "evidence": "observed"}`

#### Scenario: Layer0Check with passed=False

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Check.to_dict
- **Given** a `Layer0Check` instance with `passed=False`
- **When** `to_dict()` is called
- **Then** the result dict has `passed` equal to `False`

---

### Requirement: Layer0Result aggregation
Layer0Result SHALL aggregate multiple Layer0Check results and expose `all_passed`, `passed_count`, `failed_checks`, and `total_count` properties.

#### Scenario: Layer0Result with mixed pass and fail

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Result
- **Given** a `Layer0Result` containing 3 passed checks and 2 failed checks
- **When** properties are accessed
- **Then** `all_passed` is `False`, `passed_count` is 3, `failed_checks` has length 2, `total_count` is 5

#### Scenario: Layer0Result with all checks passed

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Result
- **Given** a `Layer0Result` containing 4 passed checks and 0 failed checks
- **When** `all_passed` is accessed
- **Then** it is `True`

---

### Requirement: spec_file_coverage check
`check_spec_file_coverage` SHALL verify that every spec file in the change's `specs/` directory has at least one corresponding code change in the git diff. When keywords from the spec filename or heading match filenames or content in the diff, the spec is considered covered.

#### Scenario: spec_file_coverage passes when spec keywords match diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change_dir with `specs/phase-cap-budget.md` containing heading "Phase Token Cap TokenBudget", and a mock transport whose git diff output contains "token_budget" in changed files
- **When** `check_spec_file_coverage` is called
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: spec_file_coverage fails when spec has no matching diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change_dir with 3 spec files but a git diff that only touches files unrelated to any spec keywords
- **When** `check_spec_file_coverage` is called
- **Then** the returned `Layer0Check` has `passed=False` and `evidence` contains the uncovered spec filenames

#### Scenario: spec_file_coverage passes when no spec files exist

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change_dir with no `specs/` directory or an empty one
- **When** `check_spec_file_coverage` is called
- **Then** the returned `Layer0Check` has `passed=True`

---

### Requirement: tasks_completion check
`check_tasks_completion` SHALL verify that all checkbox items in `tasks.md` are checked off. An empty or missing `tasks.md` SHALL be treated as a pass.

#### Scenario: tasks_completion passes when all tasks checked

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a change_dir with `tasks.md` containing only `- [x]` items
- **When** `check_tasks_completion` is called
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: tasks_completion fails with unchecked items

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a change_dir with `tasks.md` containing `- [ ]` items
- **When** `check_tasks_completion` is called
- **Then** the returned `Layer0Check` has `passed=False` and `evidence` mentions the count of unchecked items

#### Scenario: tasks_completion passes when tasks.md is missing

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a change_dir with no `tasks.md` file
- **When** `check_tasks_completion` is called
- **Then** the returned `Layer0Check` has `passed=True`

---

### Requirement: testable_not_all_false check
`check_testable_not_all_false` SHALL verify that at least one scenario across all specs has `testable=true`. If all scenarios are `testable=false` or scenarios exist but none is testable, it SHALL fail.

#### Scenario: testable_not_all_false passes with at least one testable scenario

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_testable_not_all_false
- **Given** a change_dir with a spec file containing a scenario with `- **testable**: true`
- **When** `check_testable_not_all_false` is called
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: testable_not_all_false fails when all scenarios are not testable

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_testable_not_all_false
- **Given** a change_dir with spec files where every scenario has `testable=false` or no testable field
- **When** `check_testable_not_all_false` is called
- **Then** the returned `Layer0Check` has `passed=False`

---

### Requirement: no_syntax_error check
`check_no_syntax_error` SHALL verify that all changed Python files pass `py_compile`. Files with syntax errors SHALL cause a fail.

#### Scenario: no_syntax_error passes with valid Python

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_no_syntax_error
- **Given** a target_path with changed Python files that are syntactically valid
- **When** `check_no_syntax_error` is called
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: no_syntax_error fails with syntax error in changed file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_no_syntax_error
- **Given** a target_path where a changed Python file contains a syntax error
- **When** `check_no_syntax_error` is called
- **Then** the returned `Layer0Check` has `passed=False`

---

### Requirement: spec_scenario_coverage check
`check_spec_scenario_coverage` SHALL extract key SHALL/MUST terms from spec files and verify that a sufficient proportion of these terms appear in the git diff.

#### Scenario: spec_scenario_coverage passes when key terms in diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_scenario_coverage
- **Given** a spec containing "SHALL provide phase_cap" and a git diff containing "phase_cap"
- **When** `check_spec_scenario_coverage` is called
- **Then** the returned `Layer0Check` has `passed=True`

#### Scenario: spec_scenario_coverage fails when key terms absent from diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_scenario_coverage
- **Given** a spec containing "SHALL provide get_phase_cap" but a git diff not containing that term
- **When** `check_spec_scenario_coverage` is called
- **Then** the returned `Layer0Check` has `passed=False`
