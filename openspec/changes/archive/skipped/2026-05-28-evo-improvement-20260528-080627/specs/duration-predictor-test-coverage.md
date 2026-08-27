# Duration Predictor Test Coverage

Delta spec for `zsiga/duration_predictor.py` (164 lines, 5 functions) — add a new unit
test file `tests/test_duration_predictor.py` covering the 3 private functions that lack
**direct** test coverage in `tests/test_phase_duration.py`, plus boundary cases for
`_fit_linear`.

> **Overlap avoidance** (per clarify.md):
> `tests/test_phase_duration.py` already tests `_fit_linear` (2 scenarios:
> `test_known_coefficients`, `test_empty_input`) and `predict_change_duration`
> (7 scenarios: sufficient data, insufficient data, negative clamping, missing keys).
> This spec fills the **remaining gaps**: `_collect_known_phases`, `_predict_phase`,
> `_fallback_estimates`, and `_fit_linear` boundary cases. It does **not** duplicate
> existing assertions. `predict_change_duration` is OUT of scope because it is
> already well-covered.

## ADDED Requirements

### Requirement: collect-known-phases-extracts-unique-names

`_collect_known_phases` SHALL return the set of all unique phase-name strings
found across the `phases` dictionaries of every record in the input list.
Records without a `phases` key SHALL be tolerated and contribute nothing.

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `set()`

#### Scenario: single record with one phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with `phases: {"implement": 20.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"implement"}`

#### Scenario: multiple records with overlapping phases deduplicates

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** three records whose `phases` keys are `{"explore": 10}`,
  `{"explore": 12, "design": 5}`, and `{"implement": 20}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "design", "implement"}`

#### Scenario: record without phases key contributes nothing

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record `{"project_lines": 100}` (no `phases` key)
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `set()`

---

### Requirement: fit-linear-boundary-cases

`_fit_linear` SHALL handle degenerate inputs gracefully. When the design matrix
is singular (determinant ≈ 0), it SHALL return `(0.0, 0.0, mean_y)`. When given
a single data point, it SHALL also fall back to the mean. These boundary cases
SHALL NOT duplicate the existing `test_known_coefficients` or `test_empty_input`
tests in `tests/test_phase_duration.py`.

#### Scenario: collinear inputs fall back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1 = `[1.0, 2.0, 3.0]`, xs2 = `[2.0, 4.0, 6.0]` (xs2 = 2×xs1, collinear),
  ys = `[10.0, 20.0, 30.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL equal `(0.0, 0.0, 20.0)` where 20.0 is the mean of ys

#### Scenario: single data point falls back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1 = `[5.0]`, xs2 = `[3.0]`, ys = `[42.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL equal `(0.0, 0.0, 42.0)`

#### Scenario: large values do not cause numerical overflow

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1 = `[1e8, 2e8, 3e8]`, xs2 = `[1e6, 2e6, 3e6]`,
  ys = `[1e4, 2e4, 3e4]`
- **When** `_fit_linear` is called
- **Then** the returned coefficients SHALL all be finite floats (not `inf` or `nan`)

---

### Requirement: predict-phase-returns-clamped-duration

`_predict_phase` SHALL return a non-negative float representing the predicted
duration for a single phase. With fewer than 3 matching records it SHALL fall
back to the median of available values, or `DEFAULT_PHASE_SECONDS` (30.0) when
no records match. With 3+ records it SHALL use linear regression via
`_fit_linear` and clamp negative predictions to 0.0.

#### Scenario: no matching records returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records that all contain phase `"explore"` but not `"deliver"`
- **When** `_predict_phase` is called with `phase_name="deliver"`
- **Then** the result SHALL equal `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: single matching record returns that value

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 1 record with phase `"explore"` duration `7.5`
- **When** `_predict_phase` is called for phase `"explore"`
- **Then** the result SHALL equal `7.5`

#### Scenario: two matching records returns median fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with phase `"explore"` durations `[10.0, 20.0]`
- **When** `_predict_phase` is called for phase `"explore"`
- **Then** the result SHALL equal `15.0` (median of [10.0, 20.0])

#### Scenario: three or more matching records produces non-negative prediction

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with phase `"explore"` and durations `[10.0, 12.0, 11.0]`
  at `project_lines` [1000, 2000, 1500] and `proposal_chars` [500, 600, 550]
- **When** `_predict_phase` is called for `"explore"` with
  `project_lines=1500, proposal_chars=550`
- **Then** the result SHALL be a `float >= 0.0`

#### Scenario: record missing target phase is skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records where only 2 contain phase `"implement"` with durations
  `[20.0, 30.0]`, and the third record lacks `"implement"` entirely
- **When** `_predict_phase` is called for `"implement"`
- **Then** the result SHALL equal `25.0` (median of [20.0, 30.0], since only
  2 matching records trigger fallback path)

---

### Requirement: fallback-estimates-computes-median-per-phase

`_fallback_estimates` SHALL return a dict mapping every known phase to its
median duration across all records (using `DEFAULT_PHASE_SECONDS` when a phase
has no durations), plus a `_total` key equal to the sum of all per-phase values.

#### Scenario: empty input returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: single record returns its phase durations

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** one record with `phases: {"explore": 12.0, "implement": 25.0}`
- **When** `_fallback_estimates` is called
- **Then** `result["explore"]` SHALL equal `12.0`
- **And** `result["implement"]` SHALL equal `25.0`
- **And** `result["_total"]` SHALL equal `37.0`

#### Scenario: multiple records computes correct median per phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records:
  - `{"phases": {"explore": 10.0, "design": 5.0}}`
  - `{"phases": {"explore": 20.0, "design": 10.0}}`
- **When** `_fallback_estimates` is called
- **Then** `result["explore"]` SHALL equal `15.0` (median of [10, 20])
- **And** `result["design"]` SHALL equal `7.5` (median of [5, 10])
- **And** `result["_total"]` SHALL equal `22.5`

#### Scenario: _total always equals sum of per-phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** three records with mixed phases
  (explore+design, explore+implement, explore+design+verify)
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` SHALL equal the sum of all values whose keys
  are not `"_total"`
