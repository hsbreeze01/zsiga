# Delta Spec: Duration Predictor Unit Tests

## ADDED Requirements

### Requirement: `_collect_known_phases` direct unit coverage

The test file `tests/test_duration_predictor.py` SHALL exercise
`zsiga/duration_predictor._collect_known_phases` directly, covering:

1. Normal multi-phase input returns the union of all phase-name keys.
2. Empty input returns an empty set.
3. Single-record input returns exactly the keys of that record's `phases` dict.
4. Records with overlapping phase names produce a deduplicated set.

#### Scenario: collect phases from multiple records with overlapping keys

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of two records where the first has `phases={"enrich": 5, "implement": 10}` and the second has `phases={"implement": 8, "verify": 7}`
- **When** `_collect_known_phases` is called with that list
- **Then** the returned set equals `{"enrich", "implement", "verify"}`

#### Scenario: collect phases from empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the returned set equals `set()` (empty set)

#### Scenario: collect phases from records missing the `phases` key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing a record with no `phases` key, e.g. `[{"project_lines": 100}]`
- **When** `_collect_known_phases` is called
- **Then** the returned set equals `set()` (empty set) — `dict.get("phases", {})` returns `{}`

---

### Requirement: `_predict_phase` direct unit coverage

The test file SHALL exercise `zsiga.duration_predictor._predict_phase` directly:

1. With ≥3 matching records, the function returns a regression-based prediction ≥ 0.
2. With 1–2 matching records, the function returns the median of available durations.
3. With 0 matching records, the function returns `DEFAULT_PHASE_SECONDS` (30.0).
4. Predictions are clamped to ≥ 0.0.

#### Scenario: regression path with 3+ matching records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 4 records with non-collinear `project_lines`/`proposal_chars` features, all containing phase `"implement"` with durations `[10.0, 30.0, 15.0, 50.0]`
- **When** `_predict_phase` is called for phase `"implement"` with target `project_lines=2500, proposal_chars=300`
- **Then** the returned value is a non-negative float (regression is used since ≥3 records exist with non-degenerate features)

#### Scenario: median fallback with exactly 2 matching records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 2 records with phase `"verify"` durations `[10.0, 20.0]`
- **When** `_predict_phase` is called for phase `"verify"`
- **Then** the returned float equals `15.0` (median of [10, 20])

#### Scenario: no matching records returns default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of records that do NOT contain phase `"deliver"`
- **When** `_predict_phase` is called for phase `"deliver"`
- **Then** the returned float equals `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: single matching record returns that value

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of 1 record with phase `"enrich"` duration `42.0`
- **When** `_predict_phase` is called for phase `"enrich"`
- **Then** the returned float equals `42.0`

---

### Requirement: `_fallback_estimates` direct unit coverage

The test file SHALL exercise `zsiga.duration_predictor._fallback_estimates` directly:

1. Returns a dict with one key per known phase, plus `_total`.
2. Each value is the median of that phase's durations across records.
3. `_total` equals the sum of all per-phase values (excluding itself).
4. With no data, `_total` equals `0.0`.
5. With odd-count durations the median is the middle element; with even-count it is the arithmetic mean of the two middle elements.

#### Scenario: fallback with odd number of records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 3 records with phase `"implement"` durations `[10.0, 20.0, 30.0]`
- **When** `_fallback_estimates` is called
- **Then** the result dict contains `"implement": 20.0` and `"_total": 20.0`

#### Scenario: fallback with even number of records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 2 records with phase `"verify"` durations `[10.0, 20.0]`
- **When** `_fallback_estimates` is called
- **Then** the result dict contains `"verify": 15.0` and `"_total": 15.0`

#### Scenario: fallback with empty stats

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result dict contains only `"_total": 0.0` and no other keys

#### Scenario: fallback total equals sum of phase values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 2 records with phases `"enrich": [5.0, 15.0]` and `"implement": [10.0, 20.0]`
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` equals `result["enrich"] + result["implement"]` (i.e. `10.0 + 15.0 = 25.0`)

---

### Requirement: `_fit_linear` boundary cases

The test file SHALL include boundary-case tests for `zsiga.duration_predictor._fit_linear`
that complement existing coverage in `tests/test_phase_duration.py`:

1. All-zero inputs (degenerate determinant) return `(0.0, 0.0, 0.0)`.
2. Collinear but non-zero inputs (singular matrix) fall back to mean of `ys`.
3. Large numerical values do not cause overflow or `inf` in coefficients.

#### Scenario: all-zero xs produce zero coefficients

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1=[0,0,0]`, `xs2=[0,0,0]`, `ys=[5,10,15]`
- **When** `_fit_linear` is called
- **Then** the returned tuple is `(0.0, 0.0, 10.0)` — degenerate determinant, fallback to mean

#### Scenario: collinear xs fall back to mean of ys

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1=[1,2,3]`, `xs2=[2,4,6]` (perfectly collinear), `ys=[10,20,30]`
- **When** `_fit_linear` is called
- **Then** the returned tuple is `(0.0, 0.0, 20.0)` — singular matrix, fallback to mean of ys

#### Scenario: large values remain finite

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1=[1e9, 2e9, 3e9, 4e9, 5e9]`, `xs2=[0, 1e9, 0, 1e9, 0]`, `ys=[1e6, 2e6, 3e6, 4e6, 5e6]`
- **When** `_fit_linear` is called
- **Then** all three returned coefficients are finite floats (no `inf` or `nan`)

