# duration_predictor_coverage

Delta spec for `tests/test_duration_predictor.py`: adding dedicated unit-test coverage
for the internal functions of `zsiga/duration_predictor.py` that lack direct tests
in the existing `tests/test_phase_duration.py`.

---

## ADDED Requirements

### Requirement: _collect_known_phases direct tests

The test file SHALL import `_collect_known_phases` from `zsiga.duration_predictor`
and exercise the following scenarios so that the function's contract is verified
independently of the higher-level `predict_change_duration` path.

#### Scenario: empty input returns empty set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]` as `phase_stats`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty `set`

#### Scenario: single record with one phase

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list with one record whose `"phases"` dict contains `{"enrich": 5.0}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"enrich"}`

#### Scenario: multiple records produce union of all phase names

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records, one with phases `{explore, design}` and another with phases `{design, implement}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "design", "implement"}`

#### Scenario: records with no phases key produce no phases

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a record dict that lacks the `"phases"` key entirely
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty `set` (`.get("phases", {})` returns empty dict)

---

### Requirement: _fallback_estimates direct tests

The test file SHALL import `_fallback_estimates` from `zsiga.duration_predictor`
and verify its median-based fallback computation independently.

#### Scenario: empty phase_stats returns only _total zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain only the key `"_total"` with value `0.0`

#### Scenario: single phase with multiple records computes median

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records both containing phase `"enrich"` with durations `[10.0, 20.0]`
- **When** `_fallback_estimates` is called
- **Then** `result["enrich"]` SHALL equal `15.0` (median of two values)
- **And** `result["_total"]` SHALL equal `15.0`

#### Scenario: multiple phases each get their own median

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records with phases `{enrich: [10.0, 20.0], verify: [5.0]}`
- **When** `_fallback_estimates` is called
- **Then** `result["enrich"]` SHALL equal `15.0`
- **And** `result["verify"]` SHALL equal `5.0`
- **And** `result["_total"]` SHALL equal `20.0`

#### Scenario: _total equals sum of per-phase estimates

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records producing 3+ known phases with numeric medians
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` SHALL equal the sum of all values whose key is not `"_total"`

---

### Requirement: _predict_phase direct tests

The test file SHALL import `_predict_phase` from `zsiga.duration_predictor`
and verify its regression / fallback / clamping behaviour directly.

#### Scenario: no matching records returns default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do not contain the requested `phase_name`
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: fewer than 3 matching records returns median

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records with phase `"enrich"` having durations `[10.0, 30.0]`
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `20.0` (median of the two values)

#### Scenario: 3+ matching records uses regression result

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with a perfectly linear relationship `y = 2*x1 + 3*x2 + 1` where `xs1` and `xs2` vary independently
- **When** `_predict_phase` is called with `project_lines=1, proposal_chars=1`
- **Then** the result SHALL be close to `6.0` (within tolerance 1e-3)

#### Scenario: negative prediction clamped to zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3+ records where the linear model would predict a negative duration for the given inputs
- **When** `_predict_phase` is called
- **Then** the result SHALL be >= 0.0

---

### Requirement: _fit_linear edge-case tests

The test file SHALL exercise `_fit_linear` beyond the two tests already in
`test_phase_duration.py`, covering degenerate / collinear inputs.

#### Scenario: degenerate collinear inputs fall back to mean

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [1.0, 1.0, 1.0]`, `xs2 = [2.0, 2.0, 2.0]`, `ys = [10.0, 10.0, 10.0]`
- **When** `_fit_linear` is called
- **Then** the returned coefficients SHALL be `(0.0, 0.0, 10.0)` (mean fallback because determinant is near-zero)

#### Scenario: single data point returns mean fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [5.0]`, `xs2 = [3.0]`, `ys = [7.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 7.0)` (single-point degenerate → mean)

---

### Requirement: test file passes pytest and ruff

The test file `tests/test_duration_predictor.py` SHALL be syntactically valid,
pass `ruff check` without errors, and all `def test_` functions SHALL pass
under `python -m pytest`.

#### Scenario: pytest exits cleanly

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py` exists on disk
- **When** `python -m pytest tests/test_duration_predictor.py` is run
- **Then** the exit code SHALL be 0

#### Scenario: ruff check passes

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py` exists on disk
- **When** `python -m ruff check tests/test_duration_predictor.py` is run
- **Then** the exit code SHALL be 0

#### Scenario: no regression on existing test_phase_duration

- **testable**: true
- **target**: tests/test_phase_duration.py
- **Given** the file `tests/test_duration_predictor.py` exists on disk
- **When** `python -m pytest tests/test_phase_duration.py` is run
- **Then** the exit code SHALL be 0

