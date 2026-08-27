# duration-predictor-unit-tests

Adds direct unit-test coverage for three private functions in
`zsiga/duration_predictor.py` that currently lack independent tests:
`_collect_known_phases`, `_predict_phase`, and `_fallback_estimates`.

Existing tests in `tests/test_phase_duration.py` cover `_fit_linear` and
the public `predict_change_duration` API but exercise the three target
functions only indirectly.

---

## ADDED Requirements

### Requirement: direct unit tests for `_collect_known_phases`

The test suite SHALL contain a test file `tests/test_duration_predictor.py`
with at least one test function that imports and calls
`_collect_known_phases` directly.

#### Scenario: collect known phases from multiple records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** a `phase_stats` list with three records whose `"phases"` dicts
  contain keys `"explore"`, `"design"`, `"implement"` (with overlap)
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `{"explore", "design", "implement"}`

#### Scenario: empty phase_stats returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** an empty `phase_stats` list `[]`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `set()` (empty set)

#### Scenario: records without phases key return empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** a `phase_stats` list with one record that has no `"phases"` key
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `set()` (empty set)

---

### Requirement: direct unit tests for `_predict_phase`

The test suite SHALL contain test functions that import and call
`_predict_phase` directly, covering both the linear-regression path
(≥ 3 data points) and the median-fallback path (< 3 data points).

#### Scenario: sufficient records use linear regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** a `records` list with 5 entries where `project_lines`,
  `proposal_chars`, and `"explore"` phase duration follow the linear
  relationship `y = 2*x1 + 3*x2 + 5`
- **When** `_predict_phase(records, "explore", project_lines=1, proposal_chars=1)`
  is called
- **Then** the returned value equals `2*1 + 3*1 + 5` (i.e. `10.0`) within
  tolerance `1e-3`

#### Scenario: insufficient records fallback to median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** a `records` list with 2 entries containing `"explore"` durations
  `[10.0, 20.0]`
- **When** `_predict_phase(records, "explore", project_lines=1000, proposal_chars=500)`
  is called
- **Then** the returned value equals `15.0` (median of `[10.0, 20.0]`)

#### Scenario: zero records returns default phase seconds

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** a `records` list with 3 entries, none of which contain the
  phase `"nonexistent"`
- **When** `_predict_phase(records, "nonexistent", project_lines=1000, proposal_chars=500)`
  is called
- **Then** the returned value equals `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** a `records` list with 3 entries containing large
  `project_lines`/`proposal_chars` values and `"explore"` durations that
  would produce a negative extrapolation for tiny input sizes
- **When** `_predict_phase(records, "explore", project_lines=0, proposal_chars=0)`
  is called
- **Then** the returned value is >= 0.0

---

### Requirement: direct unit tests for `_fallback_estimates`

The test suite SHALL contain test functions that import and call
`_fallback_estimates` directly, verifying median computation, the
`_total` key, and graceful degradation on empty input.

#### Scenario: normal input produces median estimates with total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** a `phase_stats` list with 2 records, each containing
  `"explore": 10.0` and `"explore": 20.0` respectively, plus other phases
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result dict contains `"explore"` mapped to `15.0` (median),
  and a `"_total"` key whose value equals the sum of all per-phase
  estimates

#### Scenario: empty phase_stats returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** an empty `phase_stats` list `[]`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the returned dict equals `{"_total": 0.0}`

#### Scenario: mixed records with partial phase coverage

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** a `phase_stats` list with records that each contain different
  phase subsets (e.g. record 1 has `"explore"` only, record 2 has
  `"design"` only)
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result contains both `"explore"` and `"design"` keys, and
  `"_total"` equals their sum

---

### Requirement: test file passes pytest

The file `tests/test_duration_predictor.py` MUST pass `python -m pytest
tests/test_duration_predictor.py` with exit code 0, independently of any
other test file.

#### Scenario: standalone pytest run succeeds

- **testable**: true
- **target**: tests/test_duration_predictor.py

- **Given** the file `tests/test_duration_predictor.py` exists on disk
- **When** `python -m pytest tests/test_duration_predictor.py` is executed
- **Then** the process exit code is 0

#### Scenario: no overlap with existing test_phase_duration tests

- **testable**: false

- **Given** `tests/test_phase_duration.py` tests `_fit_linear` and
  `predict_change_duration`
- **When** reviewing `tests/test_duration_predictor.py`
- **Then** it does not contain test cases that duplicate the scenarios in
  `tests/test_phase_duration.py` (specifically `TestFitLinear`,
  `TestPredictChangeDurationSufficient`,
  `TestPredictChangeDurationInsufficient`, `TestNegativeClamping`,
  `TestMissingPhaseKeys`)
