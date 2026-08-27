# Spec: duration_predictor_tests

Describes the behavioral requirements for the test suite covering `zsiga/duration_predictor.py`.

## ADDED Requirements

### Requirement: test-collect-known-phases

The test suite SHALL include a test function `test__collect_known_phases` that exercises
`_collect_known_phases` from `zsiga.duration_predictor`.

#### Scenario: extract phase names from multiple records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of historical records, each containing a `"phases"` dict with various phase names
- **When** `_collect_known_phases` is called with that list
- **Then** the returned set contains every unique phase name found across all records

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list
- **When** `_collect_known_phases` is called
- **Then** the returned set is empty

#### Scenario: records missing phases key are skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing records without a `"phases"` key
- **When** `_collect_known_phases` is called
- **Then** the returned set is empty (no KeyError raised)

---

### Requirement: test-fit-linear

The test suite SHALL include a test function `test__fit_linear` that exercises
`_fit_linear` from `zsiga.duration_predictor`.

#### Scenario: well-conditioned data returns correct coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** three equal-length lists of floats where `y = 2*x1 + 3*x2 + 5`
- **When** `_fit_linear` is called with those lists
- **Then** the returned tuple `(a, b, c)` satisfies `a ≈ 2`, `b ≈ 3`, `c ≈ 5` within tolerance 1e-6

#### Scenario: empty input returns zero coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** three empty lists
- **When** `_fit_linear` is called
- **Then** the returned tuple is `(0.0, 0.0, 0.0)`

#### Scenario: degenerate collinear data falls back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** lists where `xs2` is identical to `xs1` (perfectly collinear features)
- **When** `_fit_linear` is called
- **Then** the returned tuple has `a = 0.0`, `b = 0.0`, and `c` equal to the mean of `ys`

---

### Requirement: test-predict-phase

The test suite SHALL include a test function `test__predict_phase` that exercises
`_predict_phase` from `zsiga.duration_predictor`.

#### Scenario: sufficient data uses regression and clamps negative predictions

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** at least 3 records with phase durations, `project_lines`, and `proposal_chars`
- **When** `_predict_phase` is called with those records
- **Then** the returned float is non-negative (`>= 0.0`)

#### Scenario: insufficient data falls back to median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 1 or 2 records with matching phase durations
- **When** `_predict_phase` is called
- **Then** the returned value equals the `median` of those durations

#### Scenario: no matching data returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do not contain the requested phase name
- **When** `_predict_phase` is called
- **Then** the returned value equals `DEFAULT_PHASE_SECONDS` (30.0)

---

### Requirement: test-fallback-estimates

The test suite SHALL include a test function `test__fallback_estimates` that exercises
`_fallback_estimates` from `zsiga.duration_predictor`.

#### Scenario: computes median per phase with total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list of records each with a `"phases"` dict containing durations for phases `"clarify"` and `"implement"`
- **When** `_fallback_estimates` is called
- **Then** the returned dict contains each phase name as a key with its median duration, plus a `"_total"` key equal to the sum of all per-phase values

#### Scenario: empty input returns only total of zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list
- **When** `_fallback_estimates` is called
- **Then** the returned dict contains only `"_total"` with value `0.0`

---

### Requirement: test-predict-change-duration

The test suite SHALL include a test function `test__predict_change_duration` that exercises
`predict_change_duration` from `zsiga.duration_predictor`.

#### Scenario: few records trigger fallback path

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** fewer than 3 historical records
- **When** `predict_change_duration` is called
- **Then** the result is identical to calling `_fallback_estimates` with the same input

#### Scenario: many records trigger regression path

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** at least 3 records with consistent phase data
- **When** `predict_change_duration` is called
- **Then** the returned dict contains every known phase name as a key, all values are non-negative floats, and `"_total"` equals the sum of per-phase estimates

#### Scenario: result dict always contains _total key

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** any valid list of records (including empty)
- **When** `predict_change_duration` is called
- **Then** the returned dict always contains a `"_total"` key

---

## Cross-cutting Constraints

- All tests SHALL pass under `python -m pytest tests/test_duration_predictor.py` with exit code 0.
- The test file SHALL pass `ruff check tests/test_duration_predictor.py` with no errors.
- The test file SHALL NOT import or depend on numpy or any external library not already in `requirements.txt`.
- The source module `zsiga/duration_predictor.py` SHALL NOT be modified.
