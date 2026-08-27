# duration-predictor-tests

ADDED spec: Unit tests for `zsiga/duration_predictor.py` internal functions
that lack direct coverage in existing `tests/test_phase_duration.py`.

## ADDED Requirements

### Requirement: _collect_known_phases returns unique phase names

The system SHALL correctly extract all unique phase names from a list of
historical phase-stat records. Each record contains a `"phases"` dict whose
keys are phase names.

#### Scenario: collect phases from multiple records with overlapping names

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of 3 records where `"phases"` dicts contain `{explore, design}`,
  `{design, implement}`, and `{explore, verify}` respectively
- **When** `_collect_known_phases` is called with that list
- **Then** the returned set equals `{"explore", "design", "implement", "verify"}`

#### Scenario: collect phases from empty list

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list
- **When** `_collect_known_phases` is called
- **Then** the returned set is empty

#### Scenario: collect phases ignores records without phases key

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with `{"phases": {"explore": 10.0}}` and
  one record with no `"phases"` key
- **When** `_collect_known_phases` is called
- **Then** the returned set equals `{"explore"}`

### Requirement: _predict_phase clamps negative predictions to zero

When the linear regression model produces a negative predicted duration for a
phase, the system SHALL return `0.0` instead of a negative value.

#### Scenario: prediction below zero is clamped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with linearly increasing features and durations, and a
  query with very small `project_lines` and `proposal_chars` that would produce
  a negative raw prediction
- **When** `_predict_phase` is called
- **Then** the returned value is `>= 0.0`

#### Scenario: prediction with fewer than 3 data points returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records for phase `"explore"` with durations `[10.0, 30.0]`
- **When** `_predict_phase` is called with `phase_name="explore"`
- **Then** the returned value is `20.0` (median of available durations)

#### Scenario: prediction with zero data points returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that contain no entry for phase `"unknown_phase"`
- **When** `_predict_phase` is called with `phase_name="unknown_phase"`
- **Then** the returned value is `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: prediction with sufficient data returns regression estimate

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records for phase `"implement"` with perfectly linear relationship
  `duration = 0.01 * project_lines + 0.02 * proposal_chars`
- **When** `_predict_phase` is called with `project_lines=2000, proposal_chars=500`
- **Then** the returned value equals `0.01 * 2000 + 0.02 * 500 = 30.0` (within tolerance 1e-3)

### Requirement: _fallback_estimates computes median per phase

When historical data has fewer than 3 records (insufficient for regression),
the system SHALL fall back to per-phase median estimates.

#### Scenario: fallback with 2 records produces median estimates

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 2 records: one with `{"explore": 10.0, "design": 5.0}` and one with
  `{"explore": 20.0, "design": 15.0}`
- **When** `_fallback_estimates` is called
- **Then** the result maps `"explore"` to `15.0` (median of [10,20]),
  `"design"` to `10.0` (median of [5,15]), and `"_total"` to `25.0`

#### Scenario: fallback with empty stats returns empty dict with zero total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list
- **When** `_fallback_estimates` is called
- **Then** the result equals `{"_total": 0.0}`

#### Scenario: fallback with partial phase coverage uses default for missing phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 1 record with `{"explore": 10.0}` (no `"design"` key)
- **When** `_fallback_estimates` is called
- **Then** `"explore"` maps to `10.0`, and `"_total"` equals `10.0`
  (only known phases appear in the result)
