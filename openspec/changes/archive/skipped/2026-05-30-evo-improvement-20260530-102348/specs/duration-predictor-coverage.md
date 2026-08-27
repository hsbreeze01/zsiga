# duration-predictor-coverage

Adds unit-test coverage for three internal functions in
`zsiga/duration_predictor.py` that lack direct test coverage:
`_collect_known_phases`, `_predict_phase`, and `_fallback_estimates`.

## ADDED Requirements

### Requirement: collect-known-phases-extraction

The system SHALL provide a function `_collect_known_phases(phase_stats)`
that returns a `set[str]` of all unique phase names found across every
record's ``phases`` dictionary.

#### Scenario: empty-input-returns-empty-set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `phase_stats`
- **When** `_collect_known_phases([])` is called
- **Then** the result SHALL be `set()`

#### Scenario: single-record-single-phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list with one record whose ``phases`` dict contains `{"explore": 10.0}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL be `{"explore"}`

#### Scenario: multiple-records-unique-phase-names

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records with disjoint phase sets `{"explore": 10.0}` and `{"design": 5.0, "implement": 20.0}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL be `{"explore", "design", "implement"}`

#### Scenario: records-missing-phases-key

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record without a ``phases`` key and one with `{"verify": 8.0}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL be `{"verify"}`

---

### Requirement: predict-phase-regression-and-fallback

The system SHALL provide a function `_predict_phase(records, phase_name,
project_lines, proposal_chars)` that returns a non-negative `float`
estimate for a single phase. When ≥3 matching records exist it SHALL use
linear regression via `_fit_linear`; otherwise it SHALL fall back to the
median of available durations, defaulting to `DEFAULT_PHASE_SECONDS`
(30.0) when no matching records exist.

#### Scenario: insufficient-data-fewer-than-3-matching-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records both containing phase `"explore"` with durations `[10.0, 20.0]`
- **When** `_predict_phase(records, "explore", 1000, 500)` is called
- **Then** the result SHALL be `15.0` (median of `[10.0, 20.0]`)

#### Scenario: no-matching-records-returns-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records that do NOT contain phase `"verify"`
- **When** `_predict_phase(records, "verify", 1000, 500)` is called
- **Then** the result SHALL be `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: sufficient-data-uses-regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records for phase `"implement"` with perfectly linear data `y = 0.01*x1 + 0.02*x2 + 1.0`
- **When** `_predict_phase(records, "implement", 1000, 500)` is called
- **Then** the result SHALL be approximately `21.0` (within tolerance `1e-3`)

#### Scenario: negative-prediction-clamped-to-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records for phase `"explore"` with data such that the regression would predict a negative value for very small inputs
- **When** `_predict_phase(records, "explore", 1, 1)` is called
- **Then** the result SHALL be `>= 0.0`

---

### Requirement: fallback-estimates-median-aggregation

The system SHALL provide a function `_fallback_estimates(phase_stats)`
that returns a `dict[str, float]` mapping every known phase to its median
historical duration (or `DEFAULT_PHASE_SECONDS` if no data exists for
that phase), plus a ``_total`` key equal to the sum of all per-phase
values. Phase keys SHALL appear in sorted order.

#### Scenario: empty-stats-return-only-total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `phase_stats`
- **When** `_fallback_estimates([])` is called
- **Then** the result SHALL be `{"_total": 0.0}`

#### Scenario: single-record-single-phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list with one record `{"phases": {"explore": 10.0}}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result SHALL be `{"explore": 10.0, "_total": 10.0}`

#### Scenario: multiple-records-median-calculation

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 3 records where `"design"` has durations `[5.0, 10.0, 15.0]` and `"verify"` has durations `[8.0, 12.0]`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** `result["design"]` SHALL be `10.0` (median of 3 values) and `result["verify"]` SHALL be `10.0` (median of 2 values)

#### Scenario: phases-sorted-alphabetically

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records with phases `"verify"`, `"design"`, `"implement"` (in that order)
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** iterating the non-`_total` keys SHALL yield `"design"`, `"implement"`, `"verify"` in alphabetical order

#### Scenario: total-equals-sum-of-phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records producing per-phase estimates of `{"explore": 12.0, "design": 7.5}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** `result["_total"]` SHALL equal `19.5`
