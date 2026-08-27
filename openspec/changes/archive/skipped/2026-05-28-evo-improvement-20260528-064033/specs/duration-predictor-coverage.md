# duration-predictor-coverage

Adds direct unit test coverage for three private functions in
`zsiga/duration_predictor.py` that are currently only tested indirectly
through the public `predict_change_duration` API.

## ADDED Requirements

### Requirement: _collect_known_phases returns unique phase names

The function `_collect_known_phases` SHALL accept a list of historical
record dicts (each containing a `"phases"` sub-dict) and return a `set`
of all unique phase names found across all records.

#### Scenario: collect from multiple records with overlapping phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of three records whose `"phases"` keys are
  `{"explore": 10, "design": 5}`, `{"design": 6, "implement": 20}`,
  and `{"explore": 11, "verify": 8}`
- **When** `_collect_known_phases` is called with this list
- **Then** the result SHALL equal `{"explore", "design", "implement", "verify"}`

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty `set`

#### Scenario: records without phases key are skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with a `"phases"` dict and one
  record without a `"phases"` key
- **When** `_collect_known_phases` is called
- **Then** the result SHALL contain only the phase names from the record
  that has a `"phases"` key

#### Scenario: single record single phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with `"phases": {"implement": 42.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"implement"}`

### Requirement: _predict_phase handles data sufficiency tiers

The function `_predict_phase` SHALL predict a duration for a single
phase given historical records, the phase name, and scaling parameters.
It MUST use linear regression when ≥ 3 data points are available for the
target phase, median fallback when 1–2 data points exist, and
`DEFAULT_PHASE_SECONDS` (30.0) when no data points exist.

#### Scenario: sufficient records use linear regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 4 records each containing phase `"explore"` with
  durations following `y = 0.01*x1 + 0.02*x2 + 1.0`
- **When** `_predict_phase` is called with `project_lines=1000`,
  `proposal_chars=500`
- **Then** the result SHALL be within 1.0 of `21.0`

#### Scenario: fewer than 3 records returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 3 total records, but only 2 of them contain phase
  `"design"` with durations 10.0 and 30.0
- **When** `_predict_phase` is called for `"design"`
- **Then** the result SHALL equal 20.0 (median of [10.0, 30.0])

#### Scenario: zero matching records returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 3 records that do not contain phase `"deliver"`
- **When** `_predict_phase` is called for `"deliver"`
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with very large `project_lines`/`proposal_chars`
  and small durations, producing small positive coefficients
- **When** `_predict_phase` is called with `project_lines=1`,
  `proposal_chars=1`
- **Then** the result SHALL be >= 0.0

#### Scenario: single record returns that value

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list where only 1 record contains phase `"verify"` with
  duration 42.0
- **When** `_predict_phase` is called for `"verify"`
- **Then** the result SHALL equal 42.0

### Requirement: _fallback_estimates produces median-based totals

The function `_fallback_estimates` SHALL compute per-phase median
durations from historical records and include a `"_total"` key that is
the sum of all per-phase estimates.

#### Scenario: normal input returns medians and total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list of 2 records with phase `"explore"` having durations
  10.0 and 30.0, and phase `"design"` having durations 5.0 and 15.0
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"explore"` = 20.0 (median),
  `"design"` = 10.0 (median), and `"_total"` = 30.0

#### Scenario: empty input returns total of zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: single record phase gets that value

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 2 records where `"explore"` has durations [10.0, 30.0] and
  `"implement"` has a single duration 40.0
- **When** `_fallback_estimates` is called
- **Then** `"explore"` SHALL equal 20.0, `"implement"` SHALL equal 40.0,
  and `"_total"` SHALL equal 60.0

#### Scenario: total equals sum of phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 2 records with phases `"a"`, `"b"`, `"c"` having varying
  durations
- **When** `_fallback_estimates` is called
- **Then** `"_total"` SHALL equal the sum of all other values in the
  returned dict
