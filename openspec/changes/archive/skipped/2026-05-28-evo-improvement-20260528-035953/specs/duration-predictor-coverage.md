# duration-predictor-coverage

Add direct unit-test coverage for three previously untested private functions
in `zsiga/duration_predictor.py`: `_collect_known_phases`, `_predict_phase`,
and `_fallback_estimates`.  The public entry-point `predict_change_duration`
and the helper `_fit_linear` are already covered in `test_phase_duration.py`.

---

## ADDED Requirements

### Requirement: direct-unit-test-for-_collect_known_phases

The test suite SHALL contain scenarios that exercise
`_collect_known_phases` in isolation (empty input, single record,
multiple records with overlapping phase names).

#### Scenario: empty-phase_stats-returns-empty-set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** an empty `phase_stats` list `[]`
- **When** `_collect_known_phases([])` is called
- **Then** the result SHALL be an empty `set()`

#### Scenario: single-record-single-phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** a list with one record `[{ "phases": { "enrich": 5.0 } }]`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL be `{"enrich"}`

#### Scenario: multiple-records-dedup-phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** two records with overlapping phase keys
  `[{"phases": {"enrich": 1.0, "implement": 2.0}}, {"phases": {"implement": 3.0, "verify": 4.0}}]`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL be `{"enrich", "implement", "verify"}`

---

### Requirement: direct-unit-test-for-_predict_phase

The test suite SHALL contain scenarios that exercise
`_predict_phase` in isolation, covering the regression path (≥3 data
points), the median fallback path (<3 data points), the no-data path
(returning `DEFAULT_PHASE_SECONDS`), and negative-value clamping.

#### Scenario: sufficient-records-uses-regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 historical records for phase `"implement"` with linearly
  increasing durations proportional to `project_lines`
- **When** `_predict_phase(records, "implement", 1500, 500)` is called
- **Then** the returned value SHALL be a non-negative `float` that is
  within a reasonable range of the input durations (not `DEFAULT_PHASE_SECONDS`)

#### Scenario: insufficient-records-uses-median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 2 historical records for phase `"enrich"` with durations `[10.0, 20.0]`
- **When** `_predict_phase(records, "enrich", 1000, 500)` is called
- **Then** the returned value SHALL be `15.0` (the median of `[10.0, 20.0]`)

#### Scenario: no-records-returns-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 records, none of which contain phase `"deliver"`
- **When** `_predict_phase(records, "deliver", 1000, 500)` is called
- **Then** the returned value SHALL be `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: negative-prediction-clamped-to-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 records for phase `"explore"` with durations proportional to
  very large `project_lines` and `proposal_chars`
- **When** `_predict_phase(records, "explore", 1, 1)` is called
  (predicting for a tiny project)
- **Then** the returned value SHALL be `>= 0.0`

---

### Requirement: direct-unit-test-for-_fallback_estimates

The test suite SHALL contain scenarios that exercise
`_fallback_estimates` in isolation, covering empty input, single phase,
multi-phase median computation, and `_total` consistency.

#### Scenario: empty-input-returns-empty-with-zero-total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** an empty `phase_stats` list `[]`
- **When** `_fallback_estimates([])` is called
- **Then** the result SHALL contain only the key `"_total"` with value `0.0`

#### Scenario: single-phase-single-record

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** one record `[{ "phases": { "enrich": 12.0 } }]`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result SHALL contain `"enrich": 12.0` and `"_total": 12.0`

#### Scenario: multi-phase-median-and-total-consistency

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** two records with phases `"enrich": [10.0, 20.0]` and
  `"implement": [30.0, 50.0]`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result SHALL contain `"enrich": 15.0` (median of `[10, 20]`)
  and `"implement": 40.0` (median of `[30, 50]`), and `"_total"` SHALL equal
  the sum of all per-phase values

---

### Requirement: direct-unit-test-for-_fit_linear

The test suite SHALL contain a scenario for `_fit_linear` to satisfy
BAC-02.  This duplicates coverage in `test_phase_duration.py` but is
required by the proposal acceptance criteria.

#### Scenario: perfect-linear-data-recovers-coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear

- **Given** `xs1 = [1, 2, 3, 4, 5]`, `xs2 = [0, 2, 1, 3, 4]`,
  `ys = [2*a + 3*b + 5 for each (a,b)]`
- **When** `_fit_linear(xs1, xs2, ys)` is called
- **Then** the returned coefficients `(a, b, c)` SHALL be approximately
  `(2.0, 3.0, 5.0)` within tolerance `1e-6`
