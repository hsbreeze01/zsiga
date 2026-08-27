# private-function-unit-tests

## MODIFIED Requirements

### REQ-DP-001: Direct unit tests for `_collect_known_phases`

`tests/test_phase_duration.py` SHALL contain at least 3 independent `def test_`
functions that directly invoke `_collect_known_phases` from
`zsiga.duration_predictor`, covering: empty input, normal multi-record input,
and records with overlapping phase names.

#### Scenario: Empty input returns empty set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** `phase_stats` is an empty list `[]`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL equal `set()` (an empty set)

#### Scenario: Normal input extracts all unique phase names

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** `phase_stats` is a list of 2 records where the first has phases
  `{"explore": 10.0, "design": 5.0}` and the second has phases
  `{"design": 6.0, "implement": 20.0}`
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL equal `{"explore", "design", "implement"}`

#### Scenario: Records with duplicate phase names return unique set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_collect_known_phases

- **Given** `phase_stats` is a list of 3 records all containing the same phase
  `"explore"` with different durations
- **When** `_collect_known_phases(phase_stats)` is called
- **Then** the result SHALL equal `{"explore"}` (a single-element set)

---

### REQ-DP-002: Direct unit tests for `_predict_phase`

`tests/test_phase_duration.py` SHALL contain at least 3 independent `def test_`
functions that directly invoke `_predict_phase` from
`zsiga.duration_predictor`, covering: sufficient-data regression,
insufficient-data median fallback, and no-data default fallback.

#### Scenario: Sufficient data returns regression prediction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 records with `project_lines` [1000, 2000, 3000],
  `proposal_chars` [500, 600, 700], and a target phase `"explore"` with
  durations [10.0, 12.0, 14.0] (linear relationship)
- **When** `_predict_phase(records, "explore", 1500, 550)` is called
- **Then** the result SHALL be a `float` >= 0.0, close to the linearly
  interpolated value (~11.0)

#### Scenario: Fewer than 3 data points returns median fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 2 records with the target phase `"explore"` having durations
  [10.0, 20.0]
- **When** `_predict_phase(records, "explore", 1000, 500)` is called
- **Then** the result SHALL equal `15.0` (median of [10.0, 20.0])

#### Scenario: No data for phase returns DEFAULT_PHASE_SECONDS

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 records that do not contain the phase `"nonexistent"`
- **When** `_predict_phase(records, "nonexistent", 1000, 500)` is called
- **Then** the result SHALL equal `30.0` (DEFAULT_PHASE_SECONDS)

#### Scenario: Negative prediction clamped to zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_predict_phase

- **Given** 3 records with large `project_lines` / `proposal_chars` and
  proportional durations, queried with very small (1, 1) inputs
- **When** the linear model would predict a negative value
- **Then** `_predict_phase` SHALL return `max(0.0, predicted)`, i.e. >= 0.0

---

### REQ-DP-003: Direct unit tests for `_fallback_estimates`

`tests/test_phase_duration.py` SHALL contain at least 3 independent `def test_`
functions that directly invoke `_fallback_estimates` from
`zsiga.duration_predictor`, covering: normal median computation,
empty input, and phases with missing data.

#### Scenario: Normal input returns per-phase medians plus total

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** `phase_stats` with 2 records, the first having
  `{"explore": 10.0, "design": 5.0}` and the second having
  `{"explore": 20.0, "design": 10.0}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result SHALL be `{"design": 7.5, "explore": 15.0, "_total": 22.5}`

#### Scenario: Empty input returns empty dict with zero total

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** `phase_stats` is an empty list `[]`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: Phase with no matching records uses DEFAULT_PHASE_SECONDS

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fallback_estimates

- **Given** `phase_stats` with 2 records, where phase `"explore"` appears in
  both but phase `"design"` only appears in one, and phase `"verify"` appears in
  neither but is discovered via `_collect_known_phases`
  — specifically: record 1 has `{"explore": 10.0}`, record 2 has `{"explore": 20.0}`
- **When** `_fallback_estimates(phase_stats)` is called
- **Then** the result SHALL contain `"explore": 15.0` (median) and `"_total": 15.0`

