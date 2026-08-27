# Duration Predictor Unit Tests

## ADDED Requirements

### Requirement: test-file-existence
The project SHALL contain a test file `tests/test_duration_predictor.py` that provides
unit-level coverage for all five functions in `zsiga/duration_predictor.py`.

#### Scenario: test-file-created

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project repository at `/home/zsiga/repo`
- **When** checking `Path("tests/test_duration_predictor.py").exists()`
- **Then** the result is `True`

---

### Requirement: bac-named-test-symbols
The test file SHALL contain at minimum the three test symbols
`test__collect_known_phases`, `test__fit_linear`, and `test__predict_phase`
as top-level `def` declarations.

#### Scenario: bac-symbols-exist

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py`
- **When** parsing the AST and collecting all top-level `def` names
- **Then** the set of names includes `test__collect_known_phases`,
  `test__fit_linear`, and `test__predict_phase`

---

### Requirement: collect-known-phases-correctness
`_collect_known_phases(phase_stats)` SHALL return the set of all unique
phase names found in the `"phases"` dict keys across all records.

#### Scenario: normal-multi-record-dedup

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` with three records whose `"phases"` dicts contain overlapping keys
  `{"explore": 1, "design": 2}`, `{"design": 3, "implement": 4}`, `{"explore": 5}`
- **When** calling `_collect_known_phases(phase_stats)`
- **Then** the result equals `{"explore", "design", "implement"}`

#### Scenario: empty-list-input

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` is `[]`
- **When** calling `_collect_known_phases([])`
- **Then** the result is `set()`

#### Scenario: single-record

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` with one record `{"phases": {"verify": 10.0}}`
- **When** calling `_collect_known_phases(phase_stats)`
- **Then** the result equals `{"verify"}`

---

### Requirement: fit-linear-correctness
`_fit_linear(xs1, xs2, ys)` SHALL return least-squares coefficients `(a, b, c)`
for the model `y = a*x1 + b*x2 + c`. When the design matrix determinant is
near zero (`abs(D) < 1e-12`), it SHALL return `(0.0, 0.0, mean_y)`.

#### Scenario: recover-known-coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** synthetic data generated from `y = 2*x1 + 3*x2 + 5` with ≥ 5 samples
- **When** calling `_fit_linear(xs1, xs2, ys)`
- **Then** each coefficient is within `1e-6` of the true value

#### Scenario: empty-input-returns-zeros

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1=[], xs2=[], ys=[]`
- **When** calling `_fit_linear([], [], [])`
- **Then** the result is `(0.0, 0.0, 0.0)`

#### Scenario: degenerate-collinear-returns-mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [1, 1, 1]`, `xs2 = [2, 2, 2]` (perfectly collinear), `ys = [10, 20, 30]`
- **When** calling `_fit_linear(xs1, xs2, ys)`
- **Then** the result is `(0.0, 0.0, 20.0)` — the mean of `ys`

---

### Requirement: predict-phase-correctness
`_predict_phase` SHALL use linear regression when ≥ 3 data points exist for the
target phase, and fall back to median when fewer. Negative predictions SHALL be
clamped to `0.0`. When no data exists for a phase, it SHALL return
`DEFAULT_PHASE_SECONDS`.

#### Scenario: three-plus-records-regression-path

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records with `"explore"` durations `[10, 12, 11, 13]` and varying
  `project_lines` / `proposal_chars`
- **When** calling `_predict_phase(records, "explore", 1500, 550)`
- **Then** the result is a non-negative float that is not `DEFAULT_PHASE_SECONDS`

#### Scenario: fewer-than-three-median-fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with `"explore"` durations `[10.0, 20.0]`
- **When** calling `_predict_phase(records, "explore", 100, 50)`
- **Then** the result equals `15.0` (median of `[10, 20]`)

#### Scenario: no-records-default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records where none contain `"nonexistent_phase"`
- **When** calling `_predict_phase(records, "nonexistent_phase", 100, 50)`
- **Then** the result equals `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: negative-clamped-to-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with large `project_lines`/`proposal_chars` and a phase with
  durations that cause the linear model to predict a negative for small inputs
- **When** calling `_predict_phase` with very small `project_lines=1, proposal_chars=1`
- **Then** the result is `>= 0.0`

---

### Requirement: fallback-estimates-correctness
`_fallback_estimates(phase_stats)` SHALL return a dict mapping each known phase
to its median duration across records, plus a `_total` key. When no records exist,
it SHALL return `{"_total": 0.0}`.

#### Scenario: normal-median-computation

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` with 2 records: phases `{"explore": 10, "design": 5}` and
  `{"explore": 20, "design": 10}`
- **When** calling `_fallback_estimates(phase_stats)`
- **Then** result `"explore"` equals `15.0`, result `"design"` equals `7.5`,
  and `"_total"` equals `22.5`

#### Scenario: empty-input-total-zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` is `[]`
- **When** calling `_fallback_estimates([])`
- **Then** the result equals `{"_total": 0.0}`

---

### Requirement: predict-change-duration-integration
`predict_change_duration` SHALL delegate to `_fallback_estimates` when fewer than
3 records are provided, and to per-phase `_predict_phase` regression otherwise.

#### Scenario: insufficient-records-fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 1 record with `{"phases": {"enrich": 42.0}}`
- **When** calling `predict_change_duration(phase_stats, 100, 200)`
- **Then** result `"enrich"` equals `42.0` and `"_total"` equals `42.0`

#### Scenario: sufficient-records-regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 3 records each with phases `{"explore": <duration>}` and varying
  `project_lines` / `proposal_chars`
- **When** calling `predict_change_duration(phase_stats, 1500, 550)`
- **Then** the result contains `"explore"` and `"_total"`, and all values are `>= 0.0`

---

### Requirement: minimum-test-count
The test file SHALL contain at least 3 top-level `def test_` functions.

#### Scenario: test-count-geq-3

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py`
- **When** counting `def test_` declarations via AST
- **Then** the count is `>= 3`

---

### Requirement: pytest-passes
All tests in the new test file SHALL pass.

#### Scenario: pytest-exit-zero

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project with all dependencies installed
- **When** running `python -m pytest tests/test_duration_predictor.py`
- **Then** the exit code is `0`
