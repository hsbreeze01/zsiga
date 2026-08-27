# fallback-estimates

## ADDED Requirements

### Requirement: _fallback_estimates computes median durations per phase

The `_fallback_estimates` function SHALL compute a median-based fallback estimate
for every known phase. Each phase SHALL map to the median of its historical durations,
or `DEFAULT_PHASE_SECONDS` if no data exists. The result MUST include a `_total` key.

#### Scenario: multiple records produce per-phase medians

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** 3 records with phases `"explore"` (durations: 10.0, 20.0, 30.0) and `"design"` (durations: 5.0, 15.0)
- **When** `_fallback_estimates` is called
- **Then** result `"explore"` SHALL equal `20.0` (median of [10, 20, 30])
- **And** result `"design"` SHALL equal `10.0` (median of [5, 15])
- **And** result `"_total"` SHALL equal the sum of all phase values

#### Scenario: empty phase_stats returns only _total as zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: phase present in known_phases but absent from all records uses default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records where only `"explore"` has data but `_collect_known_phases` would return `{explore, design}`
- **When** `_fallback_estimates` is called
- **Then** result `"design"` SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)
- **And** result `"explore"` SHALL be the median of its actual durations

#### Scenario: _total equals sum of per-phase estimates

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records with phases `"explore"` (median: 20.0), `"implement"` (median: 45.0), `"verify"` (median: 10.0)
- **When** `_fallback_estimates` is called
- **Then** `result["_total"]` SHALL equal `20.0 + 45.0 + 10.0` (75.0)
