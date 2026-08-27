# duration-predictor-coverage

Delta spec for supplementing unit-test coverage of `zsiga/duration_predictor.py`.

Existing tests in `tests/test_phase_duration.py` cover `_fit_linear` (2 tests)
and `predict_change_duration` (6 tests).  Three internal functions —
`_collect_known_phases`, `_predict_phase`, `_fallback_estimates` — lack direct
unit tests.  This spec defines the expected behaviours that the new test file
`tests/test_duration_predictor.py` SHALL verify.

---

## ADDED Requirements

### Requirement: collect-known-phases-extraction

`_collect_known_phases(phase_stats)` SHALL return a `set[str]` containing every
unique phase name found across the `"phases"` dicts inside the supplied records.

#### Scenario: empty-input-returns-empty-set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` is an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be the empty set `set()`

#### Scenario: single-record-single-phase

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` contains one record with `phases: {"enrich": 10.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"enrich"}`

#### Scenario: multiple-records-merged-and-deduplicated

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` contains three records whose `"phases"` keys are
  `{"enrich", "design"}`, `{"design", "implement"}`, `{"verify"}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"enrich", "design", "implement", "verify"}`

#### Scenario: missing-phases-key-treated-as-empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` contains one record **without** a `"phases"` key
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be the empty set (no KeyError raised)

---

### Requirement: fallback-estimates-median

`_fallback_estimates(phase_stats)` SHALL return a `dict[str, float]` mapping
each known phase to its median duration, plus a `"_total"` key whose value is
the sum of all per-phase values.

#### Scenario: empty-input-returns-zero-total

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` is an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: single-phase-single-record

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` contains one record with `phases: {"enrich": 42.0}`
- **When** `_fallback_estimates` is called
- **Then** `result["enrich"]` SHALL equal `42.0` and `result["_total"]` SHALL
  equal `42.0`

#### Scenario: multiple-records-independent-medians

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` contains records with phase `"enrich"` durations
  `[10.0, 30.0, 20.0]` and phase `"verify"` durations `[5.0, 15.0]`
- **When** `_fallback_estimates` is called
- **Then** `result["enrich"]` SHALL equal `20.0` (median of 3),
  `result["verify"]` SHALL equal `10.0` (median of 2), and
  `result["_total"]` SHALL equal `30.0`

#### Scenario: total-is-sum-of-phase-values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` with at least two phases each having data
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` SHALL equal the arithmetic sum of all
  non-`_total` values in the returned dict (within floating-point tolerance)

---

### Requirement: predict-phase-single-phase

`_predict_phase(records, phase_name, project_lines, proposal_chars)` SHALL
return a `float >= 0.0`.  It MUST use `DEFAULT_PHASE_SECONDS` when no matching
records exist, the `median` of matching records when fewer than 3 records are
available, and linear regression otherwise.  Negative predictions MUST be
clamped to `0.0`.

#### Scenario: no-matching-phase-returns-default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** `records` contain no entry for `phase_name="nonexistent"`
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: two-records-use-median-fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** `records` has 2 entries for the target phase with durations
  `[10.0, 20.0]`
- **When** `_predict_phase` is called with any `project_lines`/`proposal_chars`
- **Then** the result SHALL equal `15.0` (median of `[10, 20]`)

#### Scenario: three-plus-records-use-linear-regression

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** `records` has 4 entries for the target phase with non-collinear
  features (`project_lines`, `proposal_chars`) and varying durations
- **When** `_predict_phase` is called with query values well beyond the training
  range
- **Then** the result SHALL be non-negative and strictly greater than the median
  of the training durations (confirming the linear-regression path was taken)

#### Scenario: negative-prediction-clamped-to-zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** at least 3 records and `project_lines`/`proposal_chars` values that
  would cause the linear model to predict a negative value
- **When** `_predict_phase` is called
- **Then** the result SHALL be `0.0` (clamped)

#### Scenario: single-record-returns-value-itself

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** `records` has exactly 1 entry for the target phase with duration
  `42.5`
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `42.5`

---

### Requirement: fit-linear-degenerate-edge-cases

`_fit_linear` is already tested for normal and empty-input cases in
`tests/test_phase_duration.py::TestFitLinear`.  The new test file SHALL
additionally cover degenerate / collinear inputs where the normal-equation
determinant is near-zero.

#### Scenario: collinear-inputs-fallback-to-mean

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1`, `xs2`, `ys` are collinear such that `y` is a function of
  only `x1` (i.e., `xs2` is a scalar multiple of `xs1`)
- **When** `_fit_linear` is called
- **Then** the returned coefficients SHALL satisfy `a ≈ 0, b ≈ 0, c ≈ mean(ys)`

#### Scenario: all-zero-y-returns-zero-coefficients

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `ys = [0.0, 0.0, 0.0]` with any non-zero `xs1`, `xs2`
- **When** `_fit_linear` is called
- **Then** all returned coefficients `(a, b, c)` SHALL be approximately zero

#### Scenario: single-point-degenerate

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** exactly one data point `(xs1=[5.0], xs2=[3.0], ys=[10.0])`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 10.0)` (mean of the single `y`)

