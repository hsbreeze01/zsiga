# Spec: Lint Pre-Check in Implement Phase

## ADDED Requirements

### Requirement: Mechanical verification SHALL tolerate zero-changed-files gracefully

When `verify_mechanical` is called with a `since_sha` that produces no changed Python files (e.g., the implementation only modified non-Python files or the diff is empty), the function SHALL return `(True, "")` — a passing result — rather than running lint and tests against an empty target list.

#### Scenario: No Python files changed since pre-impl SHA
- **Given** `_get_changed_files()` returns an empty list for the given `since_sha`
- **When** `verify_mechanical()` is called
- **Then** the function SHALL skip both lint and test execution
- **And** SHALL return `(True, "")`

#### Scenario: Only non-Python files changed
- **Given** the git diff contains changes to `site/dashboard.html` and `openspec/changes/.../tasks.md` but no `.py` files
- **When** `verify_mechanical()` is called
- **Then** the function SHALL return `(True, "")`

### Requirement: Lint filtering SHALL only report errors on lines actually changed

When `since_sha` is provided, `_filter_lint_to_changed_lines` SHALL only surface lint errors that occur on lines that were actually added or modified in the diff. Pre-existing lint errors on unchanged lines MUST NOT cause verification failure.

#### Scenario: Pre-existing lint error on unchanged line
- **Given** `ruff check` reports an E501 error on line 42 of `zsiga/config.py`
- **And** line 42 was NOT modified since `since_sha`
- **When** `_filter_lint_to_changed_lines` processes the lint output
- **Then** the E501 error SHALL be excluded from the filtered result

#### Scenario: New lint error on changed line
- **Given** `ruff check` reports an E701 error on line 15 of `zsiga/agent/loop.py`
- **And** line 15 WAS added/modified since `since_sha`
- **When** `_filter_lint_to_changed_lines` processes the lint output
- **Then** the E701 error SHALL be included in the filtered result

### Requirement: Lint auto-fix SHALL be followed by re-check, not treated as sufficient

The current flow runs `ruff check --fix` followed by `ruff check`. The `--fix` step modifies files in place. The re-check step SHALL verify the actual state after fixes are applied. If `--fix` cannot resolve an error (e.g., E701 requires manual fix), the error SHALL appear in the re-check output and be filtered to changed lines.

#### Scenario: Auto-fix resolves a lint error
- **Given** `ruff check --fix` resolves a trailing-whitespace error on a changed line
- **When** the subsequent `ruff check` runs
- **Then** the trailing-whitespace error SHALL NOT appear in the output

#### Scenario: Auto-fix cannot resolve a lint error
- **Given** `ruff check --fix` encounters an E701 (multiple statements on one line) which it cannot auto-fix
- **When** the subsequent `ruff check` runs
- **Then** the E701 error SHALL appear in the output and be filtered to changed lines
