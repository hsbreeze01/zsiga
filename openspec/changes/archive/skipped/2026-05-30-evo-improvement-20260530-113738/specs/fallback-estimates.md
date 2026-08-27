# fallback-estimates

## ADDED Requirements

### Requirement: _fallback_estimates computes median-based estimates with _total

The function `_fallback_estimates` SHALL return a dict mapping each known phase name to its median duration (or `DEFAULT_PHASE_SECONDS` when no data exists for that phase). The dict MUST include a `"_total"` key equal to the sum of all per-phase values. Phase keys (excluding `"_total"`) SHALL appear in sorted order.

#### Scenario: empty input returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL be `{"_total": 0.0}`

#### Scenario: single record returns its values as median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** one record with `phases={"explore": 10.0, "design": 5.0}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"design": 5.0`, `"explore": 10.0`, and `"_total": 15.0`

#### Scenario: phase keys are in sorted order

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records containing phases `"verify"`, `"enrich"`, `"implement"` (unsorted)
- **When** `_fallback_estimates` is called
- **Then** iterating `result.keys()` (excluding `"_total"`) SHALL yield `"enrich"`, `"implement"`, `"verify"` in that order

#### Scenario: _total equals sum of all phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 3 records with varying phase durations for phases `"enrich"`, `"implement"`, `"verify"`
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` SHALL equal the sum of all non-`"_total"` values within floating-point tolerance (1e-6)
