# Spec: Validation Constraints

## MODIFIED Requirements

### Requirement: Change scope MUST be limited to two files

This change SHALL modify exactly two files:
1. `zsiga/metrics/dashboard.py` — only the `_phase_table` function
2. `site/dashboard.html` — only the title/hero area

#### Scenario: No modifications outside declared scope

- **Given** the diff produced by this change
- **When** listing all changed files
- **Then** the set of changed files SHALL be a subset of `{zsiga/metrics/dashboard.py, site/dashboard.html}`
- **And** no files under `zsiga/pipeline/`, `zsiga/daemon/`, `tests/`, `requirements.txt`, or `pyproject.toml` SHALL be modified

### Requirement: All existing tests and lint checks SHALL pass

After implementing the change, the full test suite and lint checker MUST pass without errors.

#### Scenario: Pytest passes

- **Given** the implementation changes are applied
- **When** `pytest` is run
- **Then** all tests SHALL pass with exit code 0

#### Scenario: Ruff check passes

- **Given** the implementation changes are applied
- **When** `ruff check` is run
- **Then** there SHALL be no lint errors
