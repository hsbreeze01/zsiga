# duration-predictor-direct-coverage

Extends test coverage for three private functions in `zsiga/duration_predictor.py`
that currently lack direct independent tests (`_collect_known_phases`, `_predict_phase`,
`_fallback_estimates`). These functions are only indirectly covered via
`predict_change_duration`; the new tests validate each function's contract in isolation.

## ADDED Requirements

### Requirement: `_collect_known_phases` phase name extraction

The system SHALL extract all unique phase names from a list of historical records,
returning them as a set of strings.

#### Scenario: empty input returns empty set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]` of phase_stats records
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty set `set()`

#### Scenario: normal input returns union of all phase names

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records with `{"phases": {"explore": 10.0, "design": 5.0}}` and `{"phases": {"design": 6.0, "implement": 20.0}}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "design", "implement"}`

#### Scenario: records missing the phases key are skipped gracefully

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a record `{"project_lines": 100}` (no `"phases"` key) and a record `{"phases": {"verify": 8.0}}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"verify"}`

---

### Requirement: `_predict_phase` single-phase duration prediction

The system SHALL predict the duration of a single phase using linear regression
when sufficient data exists (≥3 matching records), median fallback otherwise,
clamping negative predictions to 0.0.

#### Scenario: no matching phase returns default seconds

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do not contain the requested phase name `"nonexistent"`
- **When** `_predict_phase` is called with phase_name `"nonexistent"`
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: fewer than 3 matching records returns median

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with phase `"explore"` durations `[10.0, 20.0]`
- **When** `_predict_phase` is called with phase_name `"explore"`
- **Then** the result SHALL equal `15.0` (median of [10.0, 20.0])

#### Scenario: three or more matching records returns regression prediction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records for phase `"explore"` with perfectly linear relationship (`y = 2*x1 + 0*x2 + 0`)
- **When** `_predict_phase` is called with `project_lines=4, proposal_chars=0`
- **Then** the predicted result SHALL be close to `8.0` (within tolerance 1e-3)

---

### Requirement: `_fallback_estimates` median-based fallback computation

The system SHALL compute per-phase median durations from historical records,
using `DEFAULT_PHASE_SECONDS` when no data exists for a phase, and include a
`_total` key that sums all per-phase estimates.

#### Scenario: empty input returns only _total zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]` of phase_stats
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: normal input returns per-phase medians with _total

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 2 records: one with `{"explore": 10.0, "design": 5.0}` and one with `{"explore": 20.0, "design": 15.0}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"design"` with value `10.0` (median of [5.0, 15.0]), `"explore"` with value `15.0` (median of [10.0, 20.0]), and `"_total"` equal to `25.0`

#### Scenario: phase present in known phases but absent in all records gets default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 1 record with `{"phases": {"explore": 10.0}}` — "explore" is the only known phase
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"explore"` with value `10.0` and `"_total"` equal to `10.0`

