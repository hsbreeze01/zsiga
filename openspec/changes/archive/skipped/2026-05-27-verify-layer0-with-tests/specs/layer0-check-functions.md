# Spec: Layer 0 Check Functions Test Coverage

## ADDED Requirements

### Requirement: Layer0Check dataclass structure SHALL be verifiable

The `Layer0Check` dataclass SHALL store a binary check result with four fields:
`id` (str), `description` (str), `passed` (bool), `evidence` (str). Its `to_dict()`
method SHALL return an `asdict`-style dictionary with all four fields.

#### Scenario: Layer0Check construction and serialization

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Check
- **Given** a `Layer0Check` constructed with `id="spec_file_coverage"`, `description="desc"`, `passed=True`, `evidence="ev"`
- **When** `to_dict()` is called
- **Then** the result is `{"id": "spec_file_coverage", "description": "desc", "passed": True, "evidence": "ev"}`

---

### Requirement: Layer0Result SHALL aggregate check results correctly

The `Layer0Result` dataclass SHALL expose computed properties:
`all_passed` (True only when every check passed), `failed_checks` (list of failed),
`passed_count`, `total_count`, `summary_line()`, and `to_dict()`.

#### Scenario: Layer0Result with mixed pass and fail

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Result
- **Given** a `Layer0Result` containing 3 `Layer0Check` with `passed=True` and 2 with `passed=False`
- **When** properties are inspected
- **Then** `all_passed` is `False`, `passed_count` is 3, `failed_checks` has length 2, and `total_count` is 5

#### Scenario: Layer0Result with all checks passing

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::Layer0Result
- **Given** a `Layer0Result` containing only `Layer0Check` with `passed=True`
- **When** `all_passed` is inspected
- **Then** `all_passed` is `True` and `failed_checks` is empty

---

### Requirement: check_spec_file_coverage SHALL verify every spec file has a corresponding code change

`check_spec_file_coverage(change_dir, target_path, pre_impl_sha, transport)` SHALL
return a `Layer0Check` with `id="spec_file_coverage"`. When no spec files exist, it
SHALL pass with skip evidence. When spec files exist but no corresponding changes are
found, it SHALL fail and list uncovered spec names.

#### Scenario: All spec files covered by code changes

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change_dir with a spec file `specs/phase-cap-budget.md` containing a title, and a diff containing `token_budget` in changed files
- **When** `check_spec_file_coverage` is called
- **Then** the returned `Layer0Check.passed` is `True`

#### Scenario: Spec files without corresponding code changes

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_file_coverage
- **Given** a change_dir with spec files `specs/phase-cap-config.md`, `specs/phase-cap-loop.md`, `specs/phase-cap-orchestration.md` and a diff containing only `token_budget.py`
- **When** `check_spec_file_coverage` is called
- **Then** the returned `Layer0Check.passed` is `False` and evidence contains at least one uncovered spec name

---

### Requirement: check_tasks_completion SHALL verify all tasks are checked off

`check_tasks_completion(change_dir, transport)` SHALL return a `Layer0Check` with
`id="tasks_completion"`. When tasks.md is absent or empty, it SHALL pass (skip).
When all checkboxes are `[x]`, it SHALL pass. When any `- [ ]` remains, it SHALL
fail with evidence showing the count of unchecked items.

#### Scenario: All tasks completed

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a `tasks.md` containing only `- [x]` items
- **When** `check_tasks_completion` is called
- **Then** the returned `Layer0Check.passed` is `True`

#### Scenario: Incomplete tasks present

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a `tasks.md` containing `- [ ] pending item`
- **When** `check_tasks_completion` is called
- **Then** the returned `Layer0Check.passed` is `False` and evidence mentions unchecked count

#### Scenario: No tasks.md file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_tasks_completion
- **Given** a change_dir without a `tasks.md` file
- **When** `check_tasks_completion` is called
- **Then** the returned `Layer0Check.passed` is `True` with skip evidence

---

### Requirement: check_testable_not_all_false SHALL ensure at least one testable scenario

`check_testable_not_all_false(change_dir, transport)` SHALL return a `Layer0Check`
with `id="testable_not_all_false"`. When no spec files exist, it SHALL pass (skip).
When at least one scenario has `testable=true`, it SHALL pass. When all scenarios
are `testable=false`, it SHALL fail.

#### Scenario: Spec with testable scenario present

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_testable_not_all_false
- **Given** a change_dir with a spec file containing a scenario marked `testable: true`
- **When** `check_testable_not_all_false` is called
- **Then** the returned `Layer0Check.passed` is `True`

#### Scenario: All scenarios marked testable false

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_testable_not_all_false
- **Given** a change_dir with a spec file where all scenarios have `testable: false`
- **When** `check_testable_not_all_false` is called
- **Then** the returned `Layer0Check.passed` is `False`

---

### Requirement: check_no_syntax_error SHALL verify changed Python files compile

`check_no_syntax_error(target_path, pre_impl_sha, transport)` SHALL return a
`Layer0Check` with `id="no_syntax_error"`. When no Python files changed, it SHALL
pass (skip). When all changed Python files compile cleanly, it SHALL pass. When a
changed Python file has a syntax error, it SHALL fail.

#### Scenario: All changed Python files are syntactically valid

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_no_syntax_error
- **Given** a target_path where a changed Python file contains valid source `x = 1`
- **When** `check_no_syntax_error` is called
- **Then** the returned `Layer0Check.passed` is `True`

#### Scenario: Changed Python file has syntax error

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_no_syntax_error
- **Given** a target_path where a changed Python file contains `def foo(`
- **When** `check_no_syntax_error` is called
- **Then** the returned `Layer0Check.passed` is `False`

---

### Requirement: check_spec_scenario_coverage SHALL verify SHALL/MUST terms appear in diff

`check_spec_scenario_coverage(change_dir, target_path, pre_impl_sha, transport)` SHALL
return a `Layer0Check` with `id="spec_scenario_coverage"`. When no spec files exist,
it SHALL pass (skip). When spec SHALL/MUST keywords appear in the diff, it SHALL pass.
When keywords are missing, it SHALL fail.

#### Scenario: Spec SHALL terms found in diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_scenario_coverage
- **Given** a change_dir with a spec containing "SHALL provide phase_cap" and a diff containing `phase_cap`
- **When** `check_spec_scenario_coverage` is called
- **Then** the returned `Layer0Check.passed` is `True`

#### Scenario: Spec SHALL terms missing from diff

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_spec_scenario_coverage
- **Given** a change_dir with a spec containing "SHALL provide get_phase_cap" and a diff without `get_phase_cap`
- **When** `check_spec_scenario_coverage` is called
- **Then** the returned `Layer0Check.passed` is `False`

---

### Requirement: check_bac_acceptance SHALL evaluate BAC items from proposal

`check_bac_acceptance(change_dir, target_path, pre_impl_sha, transport)` SHALL parse
BAC items from `proposal.md` using the `[BAC-NN]` pattern. For each BAC, it SHALL
verify the stated assertion (symbol exists, term referenced, etc.) and return a list
of `Layer0Check` objects.

#### Scenario: BAC symbol exists in source file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a `proposal.md` containing `[BAC-01] config.py 中存在 PHASE_TOKEN_CAPS` and a `config.py` containing `PHASE_TOKEN_CAPS`
- **When** `check_bac_acceptance` is called
- **Then** the returned list contains a `Layer0Check` with `passed=True`

#### Scenario: BAC symbol missing from source file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a `proposal.md` containing `[BAC-01] loop.py 中存在 handle_cap_exceeded` and a `loop.py` without `handle_cap_exceeded`
- **When** `check_bac_acceptance` is called
- **Then** the returned list contains a `Layer0Check` with `passed=False`

---

### Requirement: run_layer0_checks SHALL execute all checks and persist results

`run_layer0_checks(change_dir, target_path, pre_impl_sha, transport)` SHALL run all
5 core checks plus BAC checks (if present), return a `Layer0Result`, and write
`verify_layer0.json` to the change directory.

#### Scenario: All Layer 0 checks pass

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::run_layer0_checks
- **Given** a change_dir with no spec files (all checks pass via skip) and no proposal.md
- **When** `run_layer0_checks` is called
- **Then** `Layer0Result.all_passed` is `True`

#### Scenario: Layer 0 check failure detected

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::run_layer0_checks
- **Given** a change_dir with a `tasks.md` containing `- [ ] pending`
- **When** `run_layer0_checks` is called
- **Then** `Layer0Result.all_passed` is `False` and `failed_checks` includes the tasks_completion check
