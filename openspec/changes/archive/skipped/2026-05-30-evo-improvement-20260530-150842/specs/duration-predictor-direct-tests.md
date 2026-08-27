# Duration Predictor — Direct Test Coverage for Private Functions

## ADDED Requirements

### Requirement: `_collect_known_phases` extracts unique phase names from historical records

The function `_collect_known_phases` SHALL traverse a list of phase stat records
and return a `set[str]` of every unique phase name found under the `"phases"` key
of each record.

Records that lack a `"phases"` key MUST be silently skipped (not raise).
An empty input list SHALL return an empty set.

#### Scenario: Empty input returns empty set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]` of phase stat records
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be `set()` (empty set)

#### Scenario: Single record with phases

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with `"phases": {"explore": 10.0, "implement": 20.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "implement"}`

#### Scenario: Multiple records produce deduplicated union

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records: one with `"phases": {"explore": 10.0}` and another with `"phases": {"implement": 20.0, "explore": 15.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "implement"}` (deduplicated)

#### Scenario: Records without phases key are skipped

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record `{"project_lines": 100}` (no `"phases"` key) and one record `{"phases": {"verify": 5.0}}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"verify"}`

---

### Requirement: `_fallback_estimates` computes median-based fallback estimates

The function `_fallback_estimates` SHALL compute per-phase median durations
from historical records, plus a `_total` key equal to the sum of all per-phase
values. An empty input list SHALL return `{"_total": 0.0}`.

#### Scenario: Empty input returns only _total equal to 0.0

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]` of phase stat records
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: Single phase single record

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a list with one record `{"phases": {"explore": 10.0}}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"explore": 10.0` and `"_total": 10.0`

#### Scenario: Multiple records produce median per phase

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** three records with `"explore"` durations `[10.0, 20.0, 30.0]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"explore": 20.0` (median of 10, 20, 30) and `"_total": 20.0`

#### Scenario: _total equals sum of all per-phase values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records yielding `"explore": 15.0` and `"implement": 25.0` as medians
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` SHALL equal `result["explore"] + result["implement"]`

---

### Requirement: `_predict_phase` predicts single-phase duration with regression fallback

The function `_predict_phase` SHALL attempt linear regression when ≥3 records
contain data for the requested phase. When fewer records are available, it SHALL
fall back to the median of available values, or `DEFAULT_PHASE_SECONDS` (30.0)
when no data exists. Negative predictions MUST be clamped to `0.0`.

#### Scenario: No matching phase returns DEFAULT_PHASE_SECONDS

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that contain only `"explore"` data
- **When** `_predict_phase` is called with `phase_name="verify"`
- **Then** the result SHALL equal `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: Fewer than 3 matching records returns median

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with `"explore"` durations `[10.0, 20.0]`
- **When** `_predict_phase` is called with `phase_name="explore"`
- **Then** the result SHALL equal `15.0` (median of [10, 20])

#### Scenario: Exactly 3 matching records uses linear regression

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with non-collinear `(project_lines, proposal_chars)` pairs and perfectly linear data for `"explore"` (y = 0.01·x1 + 0.02·x2)
- **When** `_predict_phase` is called with `project_lines=250, proposal_chars=250`
- **Then** the result SHALL be approximately `7.5` (within 1e-3 tolerance)

#### Scenario: Negative prediction clamped to zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 collinear records with large values that, when extrapolated to small inputs, predict a negative value
- **When** `_predict_phase` is called with small `project_lines` and `proposal_chars`
- **Then** the result SHALL be `>= 0.0`

#### Scenario: Single matching record returns that value

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 1 record with `"explore"` duration `42.0`
- **When** `_predict_phase` is called with `phase_name="explore"`
- **Then** the result SHALL equal `42.0` (median of single element)

---

### Requirement: `_fit_linear` handles degenerate inputs gracefully

The function `_fit_linear` SHALL return `(0.0, 0.0, 0.0)` for empty input.
For collinear / degenerate inputs (determinant ≈ 0), it SHALL fall back to
returning `(0.0, 0.0, mean_y)`. For all-zero y values, coefficients SHALL
be zero.

#### Scenario: Collinear input triggers mean fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1=`[1.0, 2.0, 3.0]`, xs2=`[2.0, 4.0, 6.0]` (perfectly collinear), ys=`[10.0, 20.0, 30.0]`
- **When** `_fit_linear` is called
- **Then** the returned `a` and `b` SHALL be `0.0` (or near-zero, < 1e-6), and `c` SHALL equal `20.0` (mean of ys)

#### Scenario: All-zero y values return zero coefficients

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** xs1=`[1.0, 2.0, 3.0]`, xs2=`[1.0, 2.0, 3.0]`, ys=`[0.0, 0.0, 0.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 0.0)`

#### Scenario: Single point triggers degenerate path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** a single data point xs1=`[5.0]`, xs2=`[3.0]`, ys=`[10.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 10.0)` (mean of single value)

