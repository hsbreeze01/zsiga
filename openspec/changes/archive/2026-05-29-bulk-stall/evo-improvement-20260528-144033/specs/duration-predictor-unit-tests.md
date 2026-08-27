# duration-predictor-unit-tests

Direct unit test coverage for three private functions in
`zsiga/duration_predictor.py` that are only indirectly covered via
`predict_change_duration` in the existing `tests/test_phase_duration.py`.

## ADDED Requirements

### Requirement: direct-unit-test-for-_collect_known_phases

The system SHALL provide a test function `test__collect_known_phases` in
`tests/test_duration_predictor.py` that directly invokes
`_collect_known_phases` and asserts its return value.

#### Scenario: collect-known-phases-from-multiple-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a `phase_stats` list containing three records whose `phases`
  dicts are `{"explore": 10, "design": 5}`, `{"design": 6}`,
  `{"implement": 20}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `{"explore", "design", "implement"}`

#### Scenario: collect-known-phases-empty-input

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty `phase_stats` list
- **When** `_collect_known_phases([])` is called
- **Then** the returned set is empty

#### Scenario: collect-known-phases-missing-phases-key

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a `phase_stats` list containing one record with no `phases`
  key and one record with `{"explore": 10}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `{"explore"}`

### Requirement: direct-unit-test-for-_predict_phase

The system SHALL provide a test function `test__predict_phase` in
`tests/test_duration_predictor.py` that directly invokes `_predict_phase`
and asserts its return value.

#### Scenario: predict-phase-with-sufficient-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** three records for phase `"explore"` with known linear
  relationship, and `project_lines=1500, proposal_chars=550`
- **When** `_predict_phase(records, "explore", 1500, 550)` is called
- **Then** the returned float is non-negative and close to the expected
  linear prediction

#### Scenario: predict-phase-insufficient-records-fallback-to-median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** two records for phase `"explore"` with durations `[10.0, 20.0]`
- **When** `_predict_phase(records, "explore", 1500, 550)` is called
- **Then** the returned value equals `15.0` (median of the two durations)

#### Scenario: predict-phase-no-records-returns-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** an empty records list
- **When** `_predict_phase([], "explore", 1500, 550)` is called
- **Then** the returned value equals `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: predict-phase-clamps-negative-to-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** three records with large project_lines/proposal_chars values
  where the linear model would predict a negative value for small inputs,
  and `project_lines=1, proposal_chars=1`
- **When** `_predict_phase(records, "explore", 1, 1)` is called
- **Then** the returned value is `>= 0.0`

### Requirement: direct-unit-test-for-_fallback_estimates

The system SHALL provide a test function `test__fallback_estimates` in
`tests/test_duration_predictor.py` that directly invokes
`_fallback_estimates` and asserts its return value.

#### Scenario: fallback-estimates-median-for-multiple-phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records: `{"phases": {"explore": 10.0, "design": 5.0}}` and
  `{"phases": {"explore": 20.0, "design": 10.0}}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result dict contains `"explore": 15.0`,
  `"design": 7.5`, and `"_total"` equal to `22.5`

#### Scenario: fallback-estimates-empty-input

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty `phase_stats` list
- **When** `_fallback_estimates([])` is called
- **Then** the result dict contains only `"_total": 0.0`

#### Scenario: fallback-estimates-single-record

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a single record with `{"explore": 10.0, "design": 5.0}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result dict contains `"explore": 10.0`,
  `"design": 5.0`, and `"_total"` equal to `15.0`

#### Scenario: fallback-estimates-phase-with-no-duration-data

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records where phase `"verify"` appears in the known phases
  set (via one record's `phases` keys) but only one record actually has a
  duration for `"verify"`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result dict includes `"verify"` with the median of available
  durations (the single value), and all other phases also have values
