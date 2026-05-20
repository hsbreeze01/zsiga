# Delta Spec: Validation Constraints

## ADDED Requirements

### Requirement: No Regressions in Test Suite

All existing tests MUST continue to pass after the changes to `_phase_table` and `dashboard.html`. No new lint violations SHALL be introduced.

#### Scenario: Full test suite passes

- **Given** the changes to `zsiga/metrics/dashboard.py` and `site/dashboard.html` are applied
- **When** `pytest tests/` is executed
- **Then** all tests SHALL pass with exit code 0

#### Scenario: Lint compliance

- **Given** the changes are applied
- **When** `ruff check zsiga/metrics/dashboard.py` is executed
- **Then** no errors or warnings SHALL be reported

#### Scenario: No modification to pipeline core

- **Given** the diff of this change
- **When** inspected
- **Then** only `zsiga/metrics/dashboard.py` and `site/dashboard.html` SHALL appear in the diff
- **And** no pipeline core logic files (daemon, phase engine, scheduler) SHALL be modified
