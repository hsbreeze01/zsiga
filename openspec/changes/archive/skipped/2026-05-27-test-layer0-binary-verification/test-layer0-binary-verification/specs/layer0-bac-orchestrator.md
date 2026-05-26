# Layer 0 BAC and Orchestrator Tests

## ADDED Requirements

### Requirement: BAC acceptance checks from proposal.md
`check_bac_acceptance` SHALL parse `[BAC-NN]` items from `proposal.md` and evaluate each one using pattern matching. Recognised patterns include:
- `` `file` 中存在 `symbol` `` — checks that symbol appears in file source
- `` `file` 中引用了 `term` `` — checks that term is referenced in file source
- `至少存在 N 个 testable=true` — counts testable=true scenarios
- `所有 spec 文件...都有对应代码变更` — delegates to spec_file_coverage
Unrecognised BAC items SHALL be skipped with `passed=True`.

#### Scenario: BAC exists pattern passes when symbol in file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md containing `[BAC-01] config.py 中存在 PHASE_TOKEN_CAPS` and mock transport returns config.py source containing `PHASE_TOKEN_CAPS`
- **When** `check_bac_acceptance` is called
- **Then** at least one returned `Layer0Check` has `id="bac_01"` and `passed=True`

#### Scenario: BAC exists pattern fails when symbol not in file

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md containing `[BAC-01] loop.py 中存在 handle_cap_exceeded` and mock transport returns loop.py source NOT containing `handle_cap_exceeded`
- **When** `check_bac_acceptance` is called
- **Then** the `bac_01` check has `passed=False`

#### Scenario: BAC reference pattern passes

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md containing `[BAC-02] orchestrator.py 中引用了 cap_exceeded` and mock transport returns source containing `cap_exceeded`
- **When** `check_bac_acceptance` is called
- **Then** the `bac_02` check has `passed=True`

#### Scenario: BAC testable count passes

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md containing `[BAC-10] 至少存在 1 个 testable=true` and a spec with at least 1 testable=true scenario
- **When** `check_bac_acceptance` is called
- **Then** the `bac_10` check has `passed=True`

#### Scenario: BAC testable count fails

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::check_bac_acceptance
- **Given** a proposal.md containing `[BAC-10] 至少存在 1 个 testable=true` but all scenarios are testable=false
- **When** `check_bac_acceptance` is called
- **Then** the `bac_10` check has `passed=False`

---

### Requirement: run_layer0_checks orchestrator
`run_layer0_checks` SHALL execute all five deterministic checks plus any BAC checks, persist results to `verify_layer0.json`, and return a `Layer0Result`.

#### Scenario: run_layer0_checks all checks pass

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::run_layer0_checks
- **Given** a mock environment where all dependencies (spec files, git diff, tasks.md, Python files, proposal.md) are configured for all checks to pass
- **When** `run_layer0_checks` is called
- **Then** the returned `Layer0Result.all_passed` is `True` and `verify_layer0.json` is written to the change_dir

#### Scenario: run_layer0_checks with partial failure

- **testable**: true
- **target**: zsiga/pipeline/verify_layer0.py::run_layer0_checks
- **Given** a mock environment where spec_file_coverage would fail (spec files exist but no matching diff)
- **When** `run_layer0_checks` is called
- **Then** the returned `Layer0Result.all_passed` is `False` and `failed_checks` includes a check with `id="spec_file_coverage"`
