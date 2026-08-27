# duration-predictor-tests

## ADDED Requirements

### Requirement: test file for duration_predictor module

The project SHALL contain a test file `tests/test_duration_predictor.py` that covers all five
functions in `zsiga/duration_predictor.py`: `_collect_known_phases`, `_fit_linear`,
`_predict_phase`, `_fallback_estimates`, and `predict_change_duration`.

Every test function MUST be independent (no shared mutable state) and pass under
`python -m pytest tests/test_duration_predictor.py` with exit code 0.

---

#### Scenario: collect_known_phases returns empty set for empty input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** an empty list of phase_stats records
- **When** `_collect_known_phases([])` is called
- **Then** the result SHALL equal `set()` (empty set)

---

#### Scenario: collect_known_phases extracts union of all phase names

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** two records where the first has phases `{clarify: 10, implement: 20}`
  and the second has phases `{implement: 15, verify: 5}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL equal `{"clarify", "implement", "verify"}`

---

#### Scenario: collect_known_phases skips records with missing phases key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** a list containing one record with a `phases` dict and one record
  with no `phases` key at all
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** only the phase names from the record that has a `phases` key
  SHALL appear in the result

---

#### Scenario: fit_linear returns zeros for empty input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear

- **Given** empty lists `xs1=[], xs2=[], ys=[]`
- **When** `_fit_linear([], [], [])` is called
- **Then** the result SHALL equal `(0.0, 0.0, 0.0)`

---

#### Scenario: fit_linear returns mean fallback for degenerate collinear data

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear

- **Given** lists where all xs1 values are identical and all xs2 values are
  identical (making the normal-equation matrix singular)
- **When** `_fit_linear(xs1, xs2, ys)` is called
- **Then** the result SHALL be `(0.0, 0.0, <mean of ys>)`

---

#### Scenario: fit_linear recovers exact coefficients for synthetic linear data

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear

- **Given** ys generated as `y = 2.0 * x1 + (-1.5) * x2 + 10.0` for varied
  non-collinear x1, x2 values
- **When** `_fit_linear(xs1, xs2, ys)` is called
- **Then** the returned coefficients SHALL equal `(2.0, -1.5, 10.0)`
  within a tolerance of `abs(actual - expected) < 1e-6`

---

#### Scenario: predict_phase returns DEFAULT_PHASE_SECONDS when no matching records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** records that do not contain the requested phase_name
- **When** `_predict_phase(records, "nonexistent_phase", 100, 500)` is called
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

---

#### Scenario: predict_phase uses median fallback with fewer than three data points

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** exactly two records that both contain the requested phase_name
  with durations `[20.0, 40.0]`
- **When** `_predict_phase(records, "clarify", 100, 500)` is called
- **Then** the result SHALL equal `median([20.0, 40.0])` = 30.0

---

#### Scenario: predict_phase uses linear regression with three or more data points

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** five records with varying `project_lines`, `proposal_chars`, and
  phase durations for phase `"clarify"`
- **When** `_predict_phase(records, "clarify", project_lines, proposal_chars)` is called
- **Then** the result SHALL be a non-negative float derived from the linear
  regression model (not the median fallback)

---

#### Scenario: predict_phase clamps negative predictions to zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** three or more records and prediction inputs that would produce a
  negative raw prediction from the linear model
- **When** `_predict_phase` is called
- **Then** the result SHALL be exactly `0.0`

---

#### Scenario: fallback_estimates returns _total=0 for empty phase_stats

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** an empty list `phase_stats=[]`
- **When** `_fallback_estimates([])` is called
- **Then** the result SHALL be `{"_total": 0.0}`

---

#### Scenario: fallback_estimates uses median for phases with data and DEFAULT for missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** records where phase "clarify" has durations `[10.0, 20.0, 30.0]`
  and phase "implement" has no data entries
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** `result["clarify"]` SHALL equal `median([10.0, 20.0, 30.0])` = 20.0,
  `result["implement"]` SHALL equal `DEFAULT_PHASE_SECONDS` (30.0),
  and `result["_total"]` SHALL equal the sum of all non-total values

---

#### Scenario: fallback_estimates _total equals sum of per-phase estimates

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** phase_stats with known phases having various durations
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** `result["_total"]` SHALL equal `sum(v for k, v in result.items() if k != "_total")`

---

#### Scenario: predict_change_duration delegates to fallback with fewer than three records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::predict_change_duration

- **Given** a list of two phase_stats records
- **When** `predict_change_duration(phase_stats, 1000, 2000)` is called
- **Then** the result SHALL be identical to calling `_fallback_estimates(phase_stats)`

---

#### Scenario: predict_change_duration uses regression per phase with three or more records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::predict_change_duration

- **Given** five phase_stats records with known phases "clarify" and "verify"
- **When** `predict_change_duration(phase_stats, project_lines, proposal_chars)` is called
- **Then** the result SHALL contain keys "clarify", "verify", and "_total",
  each per-phase value SHALL be a non-negative float, and
  `result["_total"]` SHALL equal the sum of the per-phase values

---

#### Scenario: predict_change_duration _total is consistent sum

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::predict_change_duration

- **Given** any non-empty valid phase_stats input
- **When** `predict_change_duration(phase_stats, project_lines, proposal_chars)` is called
- **Then** `result["_total"]` SHALL equal `sum(v for k, v in result.items() if k != "_total")`

