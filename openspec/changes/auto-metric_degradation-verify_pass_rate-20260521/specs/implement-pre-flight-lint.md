# Spec: Implement Phase Pre-Flight Lint Guard

## ADDED Requirements

### Requirement: Pre-flight lint on changed files before mechanical verification

After the IMPLEMENT phase completes and before mechanical verification (`verify_mechanical`) runs, the orchestrator SHALL run `ruff check` on only the files changed since `pre_sha`. If lint errors are found, the orchestrator SHALL attempt an automatic `ruff check --fix` followed by a re-check, before entering the full fix loop.

#### Scenario: Clean implementation passes pre-flight immediately

- **Given** the IMPLEMENT phase has completed and post-impl checkpoint is committed
- **And** `ruff check` on changed files returns no errors
- **When** the pre-flight lint guard runs
- **Then** it SHALL return `(passed=True, errors="")` without entering the fix loop

#### Scenario: Auto-fixable lint errors are corrected

- **Given** the IMPLEMENT phase produced code with auto-fixable lint errors (e.g., unused imports, trailing whitespace)
- **When** the pre-flight lint guard runs
- **Then** it SHALL execute `ruff check --fix` on the changed files
- **And** re-run `ruff check` to verify the fix resolved all errors
- **And** commit the auto-fixed files as a checkpoint

#### Scenario: Non-fixable lint errors trigger fix loop

- **Given** the IMPLEMENT phase produced code with lint errors that `ruff check --fix` cannot resolve (e.g., E701 single-line multiple statements)
- **When** the pre-flight lint guard runs
- **Then** after auto-fix attempt, remaining errors SHALL be passed to the existing `_fix_loop` mechanism
- **And** the fix_attempts counter SHALL include any pre-flight fix attempts

### Requirement: Pre-flight guard reports lint-only vs test-only failures distinctly

The pre-flight lint guard SHALL distinguish between lint-only failures and combined failures, so the fix loop can receive targeted error messages.

#### Scenario: Lint-only failure in pre-flight

- **Given** pre-flight lint guard finds lint errors but tests would pass
- **When** reporting to the fix loop
- **Then** the error message SHALL contain only the lint error output prefixed with `"lint:\n"`

#### Scenario: Pre-flight clean but mechanical verification finds test errors

- **Given** pre-flight lint guard passes (no lint errors)
- **When** subsequent `verify_mechanical` runs and finds test failures
- **Then** the existing fix loop SHALL handle the test failures as before
- **And** the pre-flight guard SHALL NOT interfere with test failure handling

### Requirement: Pre-flight guard is bypass-safe for non-Python changes

If no `.py` files were changed since `pre_sha`, the pre-flight lint guard SHALL return `(passed=True, errors="")` immediately without invoking `ruff`.

#### Scenario: Frontend-only change with no Python files

- **Given** all files changed since `pre_sha` are `.html` or `.css` files
- **When** the pre-flight lint guard runs
- **Then** it SHALL return `(passed=True, errors="")` immediately

### Requirement: Pre-flight lint guard has unit test coverage

The pre-flight lint guard SHALL have at minimum:
- One test for the clean-pass case
- One test for the auto-fixable case
- One test for the non-fixable case (error propagated)
- One test for the no-Python-files bypass case

#### Scenario: Test suite covers pre-flight guard

- **Given** the test suite is executed via `pytest`
- **When** the pre-flight guard tests run
- **Then** all 4 test cases SHALL pass
