# duration_predictor_direct_tests

Adds direct unit-test coverage for three private functions in
`zsiga/duration_predictor.py` that are currently only exercised
indirectly through `predict_change_duration`, plus supplementary
edge-case tests for `_fit_linear`.

## ADDED Requirements

### Requirement: _collect_known_phases direct tests

The test suite SHALL contain direct unit tests for `_collect_known_phases`
that verify its contract independently of `predict_change_duration`.

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result is an empty `set()`

#### Scenario: single record with phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record `{"phases": {"enrich": 5.0, "implement": 10.0}}`
- **When** `_collect_known_phases` is called
- **Then** the result is `{"enrich", "implement"}`

#### Scenario: multiple records with overlapping phases are deduplicated

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records, one with `{"enrich": 5.0}` and one with `{"enrich": 7.0, "implement": 10.0}`
- **When** `_collect_known_phases` is called
- **Then** the result is `{"enrich", "implement"}` with no duplicates

#### Scenario: record missing phases key yields empty contribution

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a record `{"project_lines": 100}` with no `"phases"` key
- **When** `_collect_known_phases` is called with `[record]`
- **Then** the result is an empty `set()`

---

### Requirement: _fallback_estimates direct tests

The test suite SHALL contain direct unit tests for `_fallback_estimates`
that verify its median-based computation and `_total` aggregation
independently of `predict_change_duration`.

#### Scenario: empty input returns total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result is `{"_total": 0.0}`

#### Scenario: single phase single record

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** one record `{"phases": {"enrich": 12.0}}`
- **When** `_fallback_estimates` is called
- **Then** the result contains `"enrich": 12.0` and `"_total": 12.0`

#### Scenario: multiple records compute median per phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** three records with phase `"enrich"` having durations `[10.0, 20.0, 30.0]`
- **When** `_fallback_estimates` is called
- **Then** the result contains `"enrich": 20.0` (the median)

#### Scenario: _total equals sum of per-phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records yielding `"enrich": 20.0` and `"implement": 40.0`
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` equals `60.0`, the sum of all non-`_total` values

---

### Requirement: _predict_phase direct tests

The test suite SHALL contain direct unit tests for `_predict_phase`
that verify the regression path, median fallback, default-value path,
and negative clamping — all independently of `predict_change_duration`.

#### Scenario: no matching phase returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that contain no entry for phase `"nonexistent"`
- **When** `_predict_phase` is called
- **Then** it returns `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: fewer than 3 records returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with phase `"enrich"` having durations `[10.0, 20.0]`
- **When** `_predict_phase` is called
- **Then** it returns `15.0` (the median) without invoking regression

#### Scenario: three or more records uses linear regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with non-collinear features where `y = 2*x1 + 3*x2 + 5`
  (records: `(x1,x2,y) = (1,0,7), (0,1,8), (0,0,5)`)
- **When** `_predict_phase` is called with `project_lines=100, proposal_chars=50`
- **Then** the result is approximately `355.0` (within tolerance 1e-3)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 non-collinear records `(x1,x2,y) = (1,0,1), (0,1,1), (1,1,100)`
  where the fitted model has a negative intercept
- **When** `_predict_phase` is called with `project_lines=0, proposal_chars=0`
  producing a raw negative prediction
- **Then** the result is clamped to `0.0` (never negative)

---

### Requirement: _fit_linear degenerate edge cases

The test suite SHALL contain supplementary tests for `_fit_linear`
covering the collinear-degenerate fallback and the all-zero-y path.
These tests SHALL NOT duplicate the existing `test_known_coefficients`
or `test_empty_input` in `tests/test_phase_duration.py`.

#### Scenario: collinear input falls back to mean of y

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** collinear data where `xs1` and `xs2` are perfectly proportional (determinant ≈ 0)
  and `ys = [10.0, 20.0, 30.0]`
- **When** `_fit_linear` is called
- **Then** the result is `(0.0, 0.0, 20.0)` — coefficients zeroed, `c` set to mean of `ys`

#### Scenario: all-zero y values return zero coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** non-empty `xs1`, `xs2` but `ys = [0.0, 0.0, 0.0]`
- **When** `_fit_linear` is called
- **Then** the result is `(0.0, 0.0, 0.0)`
