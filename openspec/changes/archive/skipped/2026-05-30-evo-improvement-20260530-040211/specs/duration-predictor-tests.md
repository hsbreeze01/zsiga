# duration-predictor-tests

## ADDED Requirements

### Requirement: direct-unit-tests-for-private-helpers

The module `zsiga/duration_predictor.py` exposes three private helper functions
(`_collect_known_phases`, `_predict_phase`, `_fallback_estimates`) that are
currently only tested indirectly through `predict_change_duration` in
`tests/test_phase_duration.py`. A new test file SHALL provide direct unit
tests for each of these three functions.

#### Scenario: collect-known-phases-multiple-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** a list of 3 records, each with a `"phases"` dict containing
  overlapping and distinct phase names (`"explore"`, `"design"`, `"implement"`)
- **When** `_collect_known_phases` is called with this list
- **Then** the result SHALL be the set `{"explore", "design", "implement"}`

#### Scenario: collect-known-phases-empty-list

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** an empty list
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty set

#### Scenario: collect-known-phases-single-record

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** a list containing one record with `"phases": {"verify": 8.0, "deliver": 3.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be `{"verify", "deliver"}`

#### Scenario: collect-known-phases-deduplication

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** 4 records all containing the same phase `"implement"`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL contain exactly one occurrence of `"implement"`

#### Scenario: predict-phase-sufficient-data-regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** a list of 3+ records where each has `"project_lines"`, `"proposal_chars"`,
  and a `"phases"` dict containing `"explore"` with varying durations that follow
  a linear pattern
- **When** `_predict_phase` is called for phase `"explore"`
- **Then** the returned value SHALL be a non-negative float that approximates the
  linear extrapolation for the given `project_lines` and `proposal_chars`

#### Scenario: predict-phase-insufficient-data-median-fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 2 records with durations `[10.0, 20.0]` for phase `"explore"`
- **When** `_predict_phase` is called for phase `"explore"`
- **Then** the returned value SHALL equal `15.0` (median of 10.0 and 20.0)

#### Scenario: predict-phase-no-data-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** records where the target phase `"nonexistent"` is absent
- **When** `_predict_phase` is called for that phase
- **Then** the returned value SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: predict-phase-clamp-negative

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 records with large `project_lines` / `proposal_chars` values and
  proportionally large phase durations, and a prediction request with very small
  input values (e.g., `project_lines=1, proposal_chars=1`)
- **When** the linear model would predict a negative value
- **Then** the returned value SHALL be clamped to `0.0`

#### Scenario: fallback-estimates-normal-stats

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** a list of 2 records with `"phases": {"explore": [10.0, 20.0], "design": [5.0, 15.0]}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL map `"explore"` → `15.0` (median), `"design"` → `10.0` (median),
  and `"_total"` SHALL equal the sum of all per-phase values

#### Scenario: fallback-estimates-empty-list

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** an empty list
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain only `"_total": 0.0`

#### Scenario: fallback-estimates-single-record

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** a list of 1 record with `"phases": {"verify": 8.0}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL map `"verify"` → `8.0` and `"_total"` → `8.0`

### Requirement: test-file-exists-and-passes

A new test file `tests/test_duration_predictor.py` SHALL exist, contain at least
3 `def test_` functions targeting the three private helpers, and pass under
`pytest` without regressions in the existing test suite.

#### Scenario: test-file-exists

- **testable**: true
- **target**: tests/test_duration_predictor.py

- **Given** the project repository
- **When** checking for the existence of `tests/test_duration_predictor.py`
- **Then** the file SHALL exist

#### Scenario: test-file-has-required-functions

- **testable**: true
- **target**: tests/test_duration_predictor.py

- **Given** `tests/test_duration_predictor.py`
- **When** searching for function definitions
- **Then** it SHALL contain at least one test function for each of
  `_collect_known_phases`, `_predict_phase`, and `_fallback_estimates`

#### Scenario: all-tests-pass

- **testable**: true
- **target**: tests/test_duration_predictor.py

- **Given** the project repository with all dependencies installed
- **When** `python -m pytest tests/test_duration_predictor.py` is executed
- **Then** the exit code SHALL be 0

#### Scenario: no-regression-in-existing-tests

- **testable**: true
- **target**: tests/test_phase_duration.py

- **Given** the project repository with the new test file
- **When** `python -m pytest tests/test_phase_duration.py` is executed
- **Then** the exit code SHALL be 0
