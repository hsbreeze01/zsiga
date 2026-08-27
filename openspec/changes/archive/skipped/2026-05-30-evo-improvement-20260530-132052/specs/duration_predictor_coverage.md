# duration_predictor_coverage

Covers the three internal functions of `zsiga/duration_predictor.py` that lack
dedicated test coverage in the existing `tests/test_phase_duration.py`:
`_collect_known_phases`, `_predict_phase`, and `_fallback_estimates`.

## ADDED Requirements

### Requirement: collect-known-phases

`_collect_known_phases` SHALL return the set of all unique phase names found
across every record's `"phases"` dictionary.  It MUST treat missing or empty
`"phases"` keys gracefully (contributing nothing to the result set).

#### Scenario: distinct phases from multiple records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records whose `"phases"` dicts contain disjoint keys
  `{"explore": 10.0}` and `{"design": 5.0}`
- **When** `_collect_known_phases` is called with that list
- **Then** the result equals `{"explore", "design"}`

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list of records
- **When** `_collect_known_phases` is called
- **Then** the result equals `set()`

#### Scenario: overlapping phases are deduplicated

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** three records, each containing `"implement"` in their `"phases"` dict
- **When** `_collect_known_phases` is called
- **Then** `"implement"` appears exactly once in the returned set

---

### Requirement: predict-phase

`_predict_phase` SHALL produce a non-negative duration estimate for a single
phase.  With fewer than three data points it MUST fall back to the median of
available values (or `DEFAULT_PHASE_SECONDS` when zero data points exist).

#### Scenario: fewer than three records returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** two records for phase `"explore"` with durations `10.0` and `30.0`
- **When** `_predict_phase` is called
- **Then** the result equals `20.0` (the median)

#### Scenario: zero records returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** no records containing phase `"nonexistent"`
- **When** `_predict_phase` is called
- **Then** the result equals `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: regression result is non-negative

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** at least three records for phase `"verify"` and prediction inputs
  that would mathematically yield a negative value
- **When** `_predict_phase` is called
- **Then** the returned value is `>= 0.0`

---

### Requirement: fallback-estimates

`_fallback_estimates` SHALL return a dictionary mapping every known phase to
its median duration (or `DEFAULT_PHASE_SECONDS` when no duration data exists
for that phase).  The dictionary MUST include a `"_total"` key equal to the sum
of all per-phase values.

#### Scenario: computes medians and total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records: `{"phases": {"explore": 10.0}}` and
  `{"phases": {"explore": 30.0}}`
- **When** `_fallback_estimates` is called
- **Then** `result["explore"]` equals `20.0` and `result["_total"]` equals `20.0`

#### Scenario: empty stats returns zero total

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list of phase stats
- **When** `_fallback_estimates` is called
- **Then** `result` equals `{"_total": 0.0}`

#### Scenario: total equals sum of phase estimates

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records with phases `"explore"` (median 20.0) and `"design"`
  (median 7.5)
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` equals `20.0 + 7.5` (i.e. 27.5)
