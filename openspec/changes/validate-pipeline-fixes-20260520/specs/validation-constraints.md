# Spec: validation-constraints

## ADDED Requirements

### Requirement: All changes SHALL pass lint and test checks

Every modified file MUST pass `ruff check` without errors and all existing tests in the project MUST continue to pass.

#### Scenario: Ruff lint passes on modified Python files

- **Given** `zsiga/metrics/dashboard.py` (or the file containing `_phase_table`) has been modified
- **When** `ruff check` is executed on the modified file
- **Then** no errors or warnings SHALL be reported

#### Scenario: Existing test suite passes after changes

- **Given** all modifications to `_phase_table` and `dashboard.html` have been applied
- **When** `pytest` is executed on the full test suite
- **Then** all previously passing tests SHALL continue to pass
- **And** no new test failures SHALL be introduced

### Requirement: Only permitted files SHALL be modified

The implementation MUST NOT modify any file outside the explicitly allowed set.

#### Scenario: No unauthorized files are changed

- **Given** the allowed modification targets are `zsiga/metrics/dashboard.py` (or the metrics module containing `_phase_table`) and `site/dashboard.html`
- **When** the implementation diff is reviewed
- **Then** no file outside the allowed set SHALL appear in the diff
- **And** files under `venv2/`, `pyproject.toml`, `requirements.txt`, pipeline role modules (daemon, reviewer, verifier, implementer), and the `Phase` enum definition file SHALL NOT be modified
