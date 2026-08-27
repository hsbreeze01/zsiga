# duration-predictor-tests

Adds a dedicated test file `tests/test_duration_predictor.py` covering all five
functions exported by `zsiga/duration_predictor.py`.  The primary value is
direct coverage of three previously-untested private helpers:
`_collect_known_phases`, `_predict_phase`, and `_fallback_estimates`.

---

## ADDED Requirements

### Requirement: test-file-existence

A file `tests/test_duration_predictor.py` SHALL exist at the project root
containing at least three `def test_` functions.

#### Scenario: test-file-created

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project repository at `/home/zsiga/repo`
- **When** the path `tests/test_duration_predictor.py` is checked for existence
- **Then** the file SHALL exist and contain at least 3 top-level `def test_` definitions

---

### Requirement: bac-required-test-names

The file `tests/test_duration_predictor.py` SHALL contain test functions named
`test__collect_known_phases`, `test__fit_linear`, and `test__predict_phase`.

#### Scenario: required-test-names-present

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py`
- **When** the source is scanned for function definitions
- **Then** `test__collect_known_phases`, `test__fit_linear`, and `test__predict_phase` SHALL each be present exactly once

---

### Requirement: collect-known-phases-correctness

The function `_collect_known_phases(phase_stats)` SHALL return the set of all
unique phase names found across the `"phases"` dicts in every record.

#### Scenario: empty-input-returns-empty-set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `phase_stats`
- **When** `_collect_known_phases([])` is called
- **Then** the result SHALL be an empty `set`

#### Scenario: overlapping-phases-returns-union

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records whose `"phases"` keys are `{"a": 1, "b": 2}` and `{"b": 3, "c": 4}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"a", "b", "c"}`

#### Scenario: missing-phases-key-skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with no `"phases"` key and one record with `{"x": 1}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"x"}`

---

### Requirement: fit-linear-edge-cases

The function `_fit_linear(xs1, xs2, ys)` SHALL return coefficients `(a, b, c)`
for the model `y = a*x1 + b*x2 + c`.  When the system is degenerate
(collinear inputs), it SHALL fall back to returning `(0.0, 0.0, mean_y)`.

#### Scenario: degenerate-collinear-returns-mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** collinear inputs where `xs1` equals `xs2` and `ys` are `[10.0, 20.0, 30.0]`
- **When** `_fit_linear(xs1, xs2, ys)` is called
- **Then** the result SHALL be `(0.0, 0.0, 20.0)` (mean of ys)

---

### Requirement: predict-phase-behaviour

The function `_predict_phase` SHALL return a non-negative float prediction.
When fewer than 3 data points exist for the target phase it SHALL return the
median of available values, or `DEFAULT_PHASE_SECONDS` (30.0) when zero data
points exist.

#### Scenario: no-matching-phase-returns-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records where the target phase name does not appear
- **When** `_predict_phase(records, "absent_phase", 100, 200)` is called
- **Then** the result SHALL equal `30.0` (DEFAULT_PHASE_SECONDS)

#### Scenario: one-matching-record-returns-median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records but only 1 contains the target phase with duration `42.0`
- **When** `_predict_phase(records, "design", 100, 200)` is called
- **Then** the result SHALL equal `42.0` (median of a single value)

#### Scenario: three-matching-records-regression-clamped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with the target phase, sufficient for linear regression
- **When** `_predict_phase` is called with valid inputs
- **Then** the result SHALL be a `float` that is `>= 0.0`

---

### Requirement: fallback-estimates-behaviour

The function `_fallback_estimates(phase_stats)` SHALL return a dict mapping
each known phase to its median duration, plus a `_total` key equal to the sum
of all per-phase medians.  When no data exists for a phase it SHALL use
`DEFAULT_PHASE_SECONDS`.

#### Scenario: empty-stats-returns-total-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty `phase_stats` list
- **When** `_fallback_estimates([])` is called
- **Then** the result SHALL be `{"_total": 0.0}`

#### Scenario: median-and-total-computed

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records: `{"phases": {"explore": 10.0, "design": 5.0}}` and
  `{"phases": {"explore": 20.0, "design": 15.0}}`
- **When** `_fallback_estimates` is called
- **Then** `result["explore"]` SHALL equal `15.0` (median of [10, 20]),
  `result["design"]` SHALL equal `10.0` (median of [5, 15]),
  and `result["_total"]` SHALL equal `25.0`

---

### Requirement: pytest-passes

The new test file SHALL pass independently under pytest with exit code 0, and
the existing `tests/test_phase_duration.py` SHALL continue to pass unchanged.

#### Scenario: new-file-pytest-exit-zero

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project repository with the new test file
- **When** `python -m pytest tests/test_duration_predictor.py` is executed
- **Then** the exit code SHALL be 0

#### Scenario: existing-tests-no-regression

- **testable**: true
- **target**: tests/test_phase_duration.py
- **Given** the project repository with the new test file added
- **When** `python -m pytest tests/test_phase_duration.py` is executed
- **Then** the exit code SHALL be 0
