# duration_predictor_private_coverage

Covers direct unit tests for three private functions in `zsiga/duration_predictor.py`
that are only indirectly exercised through `predict_change_duration` in existing tests.

## ADDED Requirements

### Requirement: _collect_known_phases extracts unique phase names

The function `_collect_known_phases` SHALL return the union of all phase names
found across every record's `"phases"` dictionary.

#### Scenario: multiple records with overlapping and distinct phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of three records whose `"phases"` keys contain `{"explore": 10, "design": 5}`,
  `{"design": 6, "implement": 20}`, and `{"explore": 11, "verify": 8}` respectively
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `{"explore", "design", "implement", "verify"}`

#### Scenario: empty input list

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases([])` is called
- **Then** the returned set is empty (`set()`)

#### Scenario: records without phases key

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record that has no `"phases"` key and one record
  with `"phases": {"explore": 10}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `{"explore"}`

#### Scenario: single record with single phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record with `"phases": {"implement": 20.0}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the returned set equals `{"implement"}`

---

### Requirement: _predict_phase returns clamped duration for a named phase

The function `_predict_phase` SHALL predict a duration for a single named phase
using linear regression when sufficient matching records exist (≥ 3), and fall
back to median when fewer records match. The result MUST be clamped to ≥ 0.0.

#### Scenario: insufficient matching records returns median fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of two records that both contain the phase `"explore"` with
  durations 10.0 and 30.0, plus `project_lines` and `proposal_chars` fields
- **When** `_predict_phase(records, "explore", 1500, 550)` is called
- **Then** the result equals 20.0 (median of [10.0, 30.0])

#### Scenario: zero matching records returns DEFAULT_PHASE_SECONDS

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a list of records that do NOT contain the phase `"nonexistent"`
- **When** `_predict_phase(records, "nonexistent", 1000, 500)` is called
- **Then** the result equals 30.0 (DEFAULT_PHASE_SECONDS)

#### Scenario: three matching records uses linear regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** three records with `project_lines` [1000, 2000, 1500],
  `proposal_chars` [500, 600, 550], and `"explore"` durations [10.0, 12.0, 11.0]
- **When** `_predict_phase(records, "explore", 1500, 550)` is called
- **Then** the result is a non-negative float that is close to 11.0
  (the linear model should approximate the trend)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** three records with large `project_lines` and `proposal_chars`
  that produce a positive-slope model
- **When** `_predict_phase(records, "explore", 0, 0)` is called (extreme small inputs)
- **Then** the result is >= 0.0 (clamped)

#### Scenario: records with missing target phase are skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** five records where only two contain `"verify"` with durations [8.0, 12.0]
  and the other three lack the `"verify"` key entirely
- **When** `_predict_phase(records, "verify", 1000, 500)` is called
- **Then** the result equals 10.0 (median of [8.0, 12.0], since only 2 match)

---

### Requirement: _fallback_estimates computes median-based estimates per phase

The function `_fallback_estimates` SHALL return a dict mapping each known phase
to its median duration across all records, falling back to `DEFAULT_PHASE_SECONDS`
when a phase has no duration data. The dict MUST include a `"_total"` key equal
to the sum of all per-phase estimates.

#### Scenario: multiple phases with data

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records: one with `"explore": 10, "design": 5` and another with
  `"explore": 20, "design": 15`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result maps `"explore"` to 15.0 (median of [10, 20]),
  `"design"` to 10.0 (median of [5, 15]), and `"_total"` to 25.0

#### Scenario: empty input returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates([])` is called
- **Then** the result equals `{"_total": 0.0}`

#### Scenario: phase present in known set but absent from all records uses default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records where record A has `{"explore": 10}` and record B has
  `{"explore": 20}`, but `"design"` was discovered via a record whose `"phases"`
  dict contains `"design"` as a key (e.g., a third record with
  `"phases": {"design": null}` is NOT counted; only records where the phase
  appears with a truthy value)
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** phases without duration data in any record SHALL use DEFAULT_PHASE_SECONDS

#### Scenario: single record single phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** one record with `"phases": {"implement": 42.0}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result maps `"implement"` to 42.0 and `"_total"` to 42.0

---

### Requirement: test file exists and is valid

A new test file `tests/test_duration_predictor.py` SHALL exist and pass all
pytest checks without modifying production code or existing test files.

#### Scenario: test file contains required test functions

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py`
- **When** its contents are scanned for function definitions
- **Then** it contains at least 3 `def test_` functions, including
  `test__collect_known_phases` and `test__predict_phase`

#### Scenario: test file passes pytest

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the file `tests/test_duration_predictor.py`
- **When** `python -m pytest tests/test_duration_predictor.py` is executed
- **Then** the exit code is 0

#### Scenario: new tests do not break existing tests

- **testable**: true
- **target**: tests/test_phase_duration.py
- **Given** both `tests/test_phase_duration.py` and `tests/test_duration_predictor.py`
- **When** `python -m pytest tests/test_phase_duration.py tests/test_duration_predictor.py`
  is executed
- **Then** the exit code is 0
