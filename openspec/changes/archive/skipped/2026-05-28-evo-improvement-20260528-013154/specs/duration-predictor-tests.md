# duration-predictor-tests

Unit test coverage spec for `zsiga/duration_predictor.py` — a pure-computation
module with 5 functions, 0 classes, no external dependencies beyond `statistics.median`.

## ADDED Requirements

### Requirement: test file exists

The project SHALL have a test file `tests/test_duration_predictor.py` that
verifies the behavioral contracts of all five functions in
`zsiga/duration_predictor.py`.

#### Scenario: test file is importable and contains required test functions

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project test directory
- **When** the file `tests/test_duration_predictor.py` is checked for existence and searched for function definitions
- **Then** the file exists, and it contains at least 3 `def test_` functions including `test__collect_known_phases`, `test__fit_linear`, and `test__predict_phase`

---

### Requirement: _collect_known_phases extracts unique phase names

`_collect_known_phases(phase_stats)` SHALL return the set of all unique phase
names found across the `"phases"` dicts of every record.

#### Scenario: union of phase names from multiple records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records where the first has phases `{"implement": 10, "review": 5}` and the second has phases `{"review": 8, "verify": 12}`
- **When** `_collect_known_phases` is called with that list
- **Then** it returns `{"implement", "review", "verify"}`

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list
- **When** `_collect_known_phases` is called
- **Then** it returns an empty `set`

#### Scenario: records without phases key contribute nothing

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** one record with `{"phases": {"implement": 10}}` and one record with no `"phases"` key
- **When** `_collect_known_phases` is called
- **Then** it returns `{"implement"}` without raising an error

---

### Requirement: _fit_linear solves normal equations correctly

`_fit_linear(xs1, xs2, ys)` SHALL solve the normal equations for
`y = a*x1 + b*x2 + c` via Cramer's rule and return coefficients `(a, b, c)`.

#### Scenario: exact linear data y equals 2x1 plus 3x2 plus 1

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** three data points (1,1,6), (2,1,8), (1,2,9) that satisfy `y = 2·x1 + 3·x2 + 1`
- **When** `_fit_linear([1,2,1], [1,1,2], [6,8,9])` is called
- **Then** it returns `(2.0, 3.0, 1.0)` within floating-point tolerance `1e-6`

#### Scenario: empty input returns zero triple

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** empty lists `xs1=[], xs2=[], ys=[]`
- **When** `_fit_linear` is called
- **Then** it returns `(0.0, 0.0, 0.0)`

#### Scenario: single data point triggers degenerate fallback to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** a single point `xs1=[5.0], xs2=[3.0], ys=[10.0]`
- **When** `_fit_linear` is called
- **Then** the determinant is near-zero so it returns `(0.0, 0.0, 10.0)`

---

### Requirement: _predict_phase dispatches between regression and median

`_predict_phase(records, phase_name, project_lines, proposal_chars)` SHALL
use linear regression when 3+ matching records exist, median fallback with 1–2
records, and `DEFAULT_PHASE_SECONDS` with zero records.

#### Scenario: no matching records returns DEFAULT_PHASE_SECONDS

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that contain `"implement"` but the query asks for `"nonexistent"`
- **When** `_predict_phase` is called with `phase_name="nonexistent"`
- **Then** it returns `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: one or two matching records returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** exactly 2 records with `phase_name="implement"` having durations `10.0` and `20.0`
- **When** `_predict_phase` is called
- **Then** it returns `15.0` (the median of `[10.0, 20.0]`)

#### Scenario: three or more matching records returns clamped regression result

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records matching `phase_name="implement"` with varying features
- **When** `_predict_phase` is called with `project_lines=200, proposal_chars=1000`
- **Then** it returns a `float >= 0.0` derived from the linear regression (not the median fallback)

#### Scenario: negative regression prediction is clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records and input parameters that would produce a negative linear prediction
- **When** `_predict_phase` is called
- **Then** it returns `0.0` (the prediction is clamped to non-negative)

---

### Requirement: _fallback_estimates computes median-based estimates

`_fallback_estimates(phase_stats)` SHALL return a dict mapping each known phase
to its median duration, plus a `_total` key equal to the sum of all phase values.

#### Scenario: valid data returns medians and correct total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records with phases `{"implement": 10, "review": 5}` and `{"implement": 20, "review": 15}`
- **When** `_fallback_estimates` is called
- **Then** the result contains `"implement": 15.0`, `"review": 10.0`, and `"_total": 25.0`

#### Scenario: empty input returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list
- **When** `_fallback_estimates` is called
- **Then** it returns `{"_total": 0.0}`

---

### Requirement: predict_change_duration is the main entry point

`predict_change_duration(phase_stats, project_lines, proposal_chars)` SHALL
delegate to `_fallback_estimates` when `len(phase_stats) < 3` and use
per-phase regression otherwise, always including a correct `_total`.

#### Scenario: fewer than 3 records delegates to fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 1 phase_stats record
- **When** `predict_change_duration` is called
- **Then** the result is identical to `_fallback_estimates(phase_stats)`

#### Scenario: 3 or more records uses regression with correct total

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 3 records with phases `"implement"` and `"review"`
- **When** `predict_change_duration` is called
- **Then** the result contains both phase names with `float >= 0.0` values, and `"_total"` equals the sum of all other values

#### Scenario: _total invariant holds for any input

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** any valid phase_stats list (empty, small, or large)
- **When** `predict_change_duration` returns its result dict
- **Then** the `"_total"` value equals the sum of all dict values except `"_total"` itself, within tolerance `1e-6`
