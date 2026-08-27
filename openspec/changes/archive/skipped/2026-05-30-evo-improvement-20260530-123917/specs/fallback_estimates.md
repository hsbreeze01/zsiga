# fallback_estimates

## ADDED Requirements

### Requirement: _fallback_estimates computes per-phase median durations

The `_fallback_estimates` function SHALL compute a median-based estimate for
each known phase. The output dict MUST contain every known phase (sorted
alphabetically by key) plus a `"_total"` key equal to the sum of all per-phase
values. When a phase has no recorded durations, its value SHALL be
`DEFAULT_PHASE_SECONDS` (30.0).

#### Scenario: empty stats returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL be `{"_total": 0.0}`

#### Scenario: single record returns phase values directly

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** a single record `{"phases": {"explore": 10.0, "design": 5.0}}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"explore": 10.0`, `"design": 5.0`, and `"_total": 15.0`

#### Scenario: multiple records compute median per phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records: `{"phases": {"explore": 10.0}}` and `{"phases": {"explore": 20.0}}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"explore": 15.0` (median of [10, 20]) and `"_total": 15.0`

#### Scenario: keys are sorted alphabetically

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records with phases `"verify"`, `"design"`, `"implement"`
- **When** `_fallback_estimates` is called
- **Then** the non-`_total` keys SHALL appear in alphabetical order (`design`, `implement`, `verify`) when iterating `dict.keys()`
