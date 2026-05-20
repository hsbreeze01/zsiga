# Delta Spec: Validation Constraints

## ADDED Requirements

### Requirement: No Regressions in Test Suite

All existing tests MUST continue to pass after the changes to `_phase_table` and `dashboard.html`. No new lint violations SHALL be introduced.

#### Scenario: Full test suite passes

- **Given** the changes to `zsiga/metrics/dashboard.py` and `site/dashboard.html` are applied
- **When** `pytest tests/test_dashboard_api.py` is executed
- **Then** all tests SHALL pass with exit code 0

#### Scenario: Lint compliance

- **Given** the changes are applied
- **When** `ruff check zsiga/metrics/dashboard.py` is executed
- **Then** no errors or warnings SHALL be reported

#### Scenario: Scope confinement

- **Given** the diff of this change
- **When** inspected
- **Then** only `zsiga/metrics/dashboard.py` and `site/dashboard.html` SHALL appear in the diff
- **And** no pipeline core logic files (daemon, phase engine, scheduler, orchestrator) SHALL be modified
- **And** no `tests/` files SHALL be modified
- **And** no `requirements.txt` or `pyproject.toml` changes SHALL be introduced
- **And** no data acquisition or metrics computation logic outside `_phase_table` SHALL be modified

#### Scenario: Phase enumeration unchanged

- **Given** the Phase enumeration file
- **When** the diff is inspected
- **Then** the Phase enumeration definition SHALL NOT be modified
- **Note** If CLARIFY / ENRICH / OPTIMIZE are already present in the enum, no change is needed. If missing, this constraint MAY be relaxed per clarify.md "已知风险"
