# duration_predictor_unit_tests

## ADDED Requirements

### Requirement: direct-unit-tests-for-_collect_known_phases

The test suite SHALL include direct unit tests for `_collect_known_phases` that verify:
- Extraction of unique phase names from multiple records
- Empty input returns an empty set
- Single record with multiple phases
- Duplicate phase names across records are deduplicated

#### Scenario: collect-phases-from-multiple-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of 3 records where each contains a `phases` dict with overlapping and unique keys
- **When** `_collect_known_phases` is called
- **Then** the result is a set containing all unique phase names across all records

#### Scenario: collect-phases-from-empty-input

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list
- **When** `_collect_known_phases` is called
- **Then** the result is an empty set

#### Scenario: collect-phases-deduplication

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** 3 records all containing the same phase name `"implement"`
- **When** `_collect_known_phases` is called
- **Then** the result set contains exactly one element: `"implement"`

---

### Requirement: direct-unit-tests-for-_fallback_estimates

The test suite SHALL include direct unit tests for `_fallback_estimates` that verify:
- Median computation from historical durations
- Empty input produces `{ "_total": 0.0 }`
- Single-phase single-record returns that duration
- Multi-phase records compute per-phase medians independently
- `_total` equals the sum of all per-phase estimates

#### Scenario: fallback-median-from-multiple-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list of 3 records each containing phase `"enrich"` with durations 10.0, 20.0, 30.0
- **When** `_fallback_estimates` is called
- **Then** the result maps `"enrich"` to 20.0 (the median) and `"_total"` to 20.0

#### Scenario: fallback-empty-input

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list
- **When** `_fallback_estimates` is called
- **Then** the result is `{ "_total": 0.0 }`

#### Scenario: fallback-total-equals-sum-of-phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records containing phases `"explore"` (median 15.0) and `"design"` (median 7.5)
- **When** `_fallback_estimates` is called
- **Then** `"_total"` equals 22.5 (the sum of all per-phase medians)

---

### Requirement: direct-unit-tests-for-_predict_phase

The test suite SHALL include direct unit tests for `_predict_phase` that verify:
- Sufficient records (>= 3) produce a regression-based prediction clamped to >= 0.0
- Fewer than 3 records for the target phase return the median (or DEFAULT_PHASE_SECONDS if zero records)
- The coefficients from `project_lines` and `proposal_chars` influence the prediction

#### Scenario: predict-phase-with-sufficient-records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records where phase `"implement"` durations correlate linearly with project_lines
- **When** `_predict_phase` is called with a new project_lines value
- **Then** the returned prediction is >= 0.0 and approximates the linear trend

#### Scenario: predict-phase-insufficient-records-returns-median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with phase `"implement"` durations 20.0 and 40.0
- **When** `_predict_phase` is called for `"implement"`
- **Then** the result is 30.0 (the median of available durations)

#### Scenario: predict-phase-zero-records-returns-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do NOT contain the target phase `"nonexistent"`
- **When** `_predict_phase` is called for `"nonexistent"`
- **Then** the result is `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: predict-phase-negative-clamped-to-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with large project_lines/proposal_chars values and a linearly increasing phase duration
- **When** `_predict_phase` is called with very small project_lines and proposal_chars values that would produce a negative prediction
- **Then** the result is 0.0 (clamped)

---

### Requirement: edge-case-tests-for-_fit_linear

The test suite SHALL include edge-case unit tests for `_fit_linear` beyond the existing `TestFitLinear` coverage in `test_phase_duration.py`. These SHALL verify:
- Collinear input (determinant ≈ 0) returns `(0.0, 0.0, mean_y)`
- Single data point input returns `(0.0, 0.0, mean_y)` (degenerate)
- All-zero input returns `(0.0, 0.0, 0.0)` (already covered by existing test but included as baseline)

#### Scenario: fit-linear-collinear-input

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1 = [1.0, 2.0, 3.0], xs2 = [2.0, 4.0, 6.0] (xs2 = 2 * xs1, perfectly collinear), ys = [5.0, 10.0, 15.0]
- **When** `_fit_linear` is called
- **Then** the determinant is near zero and the result is `(0.0, 0.0, mean_y)` where mean_y = 10.0

#### Scenario: fit-linear-single-point

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1 = [1.0], xs2 = [1.0], ys = [5.0]
- **When** `_fit_linear` is called
- **Then** the determinant is 0.0 and the result is `(0.0, 0.0, 5.0)` (degenerate fallback to mean)

#### Scenario: fit-linear-three-non-collinear-points-exact

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** 3 non-collinear data points that satisfy y = 3*x1 - 1*x2 + 2
- **When** `_fit_linear` is called
- **Then** the returned coefficients (a, b, c) recover the exact values within floating-point tolerance
