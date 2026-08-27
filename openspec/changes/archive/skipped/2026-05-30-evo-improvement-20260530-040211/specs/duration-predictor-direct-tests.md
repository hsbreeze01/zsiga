# duration-predictor-direct-tests

## ADDED Requirements

### REQ-DP-001: Direct unit test coverage for `_collect_known_phases`

The module `zsiga/duration_predictor.py` SHALL have direct unit tests for the
private function `_collect_known_phases`.  The function extracts all unique
phase names from a list of historical records and returns them as a `set[str]`.

#### Scenario: Multiple records with overlapping phases returns deduplicated set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of three records where each contains a `"phases"` dict with
  overlapping keys `"explore"` and `"design"`, and one record also contains
  `"implement"`
- **When** `_collect_known_phases` is called with this list
- **Then** the returned set equals `{"explore", "design", "implement"}`

#### Scenario: Empty list returns empty set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list
- **When** `_collect_known_phases` is called with `[]`
- **Then** the returned set equals `set()`

#### Scenario: Single record returns all its phase keys

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list with one record whose `"phases"` dict has keys
  `"explore"` and `"verify"`
- **When** `_collect_known_phases` is called with this list
- **Then** the returned set equals `{"explore", "verify"}`

#### Scenario: Record missing phases key is treated as empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record without a `"phases"` key and one
  record with `"phases": {"deliver": 5.0}`
- **When** `_collect_known_phases` is called with this list
- **Then** the returned set equals `{"deliver"}`

---

### REQ-DP-002: Direct unit test coverage for `_predict_phase`

The module `zsiga/duration_predictor.py` SHALL have direct unit tests for the
private function `_predict_phase`.  The function predicts a single phase's
duration using linear regression when ≥3 data points are available, or the
median of available durations as a fallback, clamped to ≥0.

#### Scenario: Three or more records for target phase uses regression path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 4 records each containing `"explore"` phase durations,
  along with `"project_lines"` and `"proposal_chars"` fields
- **When** `_predict_phase` is called with `records`, `"explore"`,
  `project_lines=1500`, `proposal_chars=550`
- **Then** the returned float is ≥0 and is NOT equal to the median of the
  durations (confirming the regression path was taken, not the fallback)

#### Scenario: Fewer than three records returns median

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 2 records with `"explore"` durations of 10.0 and 30.0
- **When** `_predict_phase` is called with `records`, `"explore"`,
  `project_lines=1000`, `proposal_chars=500`
- **Then** the returned value equals 20.0 (the median of [10.0, 30.0])

#### Scenario: No records contain target phase returns default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 2 records that have `"explore"` but NOT `"deliver"`
- **When** `_predict_phase` is called with `records`, `"deliver"`,
  `project_lines=1000`, `proposal_chars=500`
- **Then** the returned value equals `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: Negative regression prediction is clamped to zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with large `project_lines`/`proposal_chars` producing a
  linear model that extrapolates negatively for very small inputs
- **When** `_predict_phase` is called with `project_lines=0`,
  `proposal_chars=0`
- **Then** the returned value is ≥0.0

---

### REQ-DP-003: Direct unit test coverage for `_fallback_estimates`

The module `zsiga/duration_predictor.py` SHALL have direct unit tests for the
private function `_fallback_estimates`.  The function computes median-based
fallback estimates for all known phases and returns a dict with a `_total` key.

#### Scenario: Normal phase_stats returns per-phase medians and correct total

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list of 3 records with phases `"explore"` and `"design"`,
  each having multiple duration values
- **When** `_fallback_estimates` is called with this list
- **Then** the result contains keys `"explore"`, `"design"`, and `"_total"`,
  each phase value equals the median of its durations, and `"_total"` equals
  the sum of the phase values

#### Scenario: Empty list returns dict with only _total equal to zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list
- **When** `_fallback_estimates` is called with `[]`
- **Then** the returned dict contains only `"_total": 0.0`

#### Scenario: Single record median equals the only value

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list with one record containing `"phases": {"verify": 42.0}`
- **When** `_fallback_estimates` is called with this list
- **Then** the result contains `"verify": 42.0` and
  `"_total": 42.0`

