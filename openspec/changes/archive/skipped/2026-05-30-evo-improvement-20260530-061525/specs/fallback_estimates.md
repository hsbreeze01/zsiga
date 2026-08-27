# fallback_estimates

## ADDED Requirements

### Requirement: _fallback_estimates computes per-phase median durations

`_fallback_estimates` SHALL compute median-based fallback estimates for each known phase extracted from `phase_stats`. Each phase with at least one recorded duration SHALL map to its median; phases with no duration data SHALL NOT appear (since they are discovered only from actual records). The result SHALL include a `"_total"` key equal to the sum of all per-phase estimates.

#### Scenario: empty_stats_returns_only_total_zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty `phase_stats` list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL be `{"_total": 0.0}`

#### Scenario: single_record_returns_phase_value

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` with one record `{"phases": {"enrich": 15.0}}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `{"enrich": 15.0, "_total": 15.0}`

#### Scenario: multiple_records_computes_median_per_phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats` with three records:
  - `{"phases": {"enrich": 10.0, "implement": 20.0}}`
  - `{"phases": {"enrich": 30.0, "implement": 40.0}}`
  - `{"phases": {"enrich": 20.0, "implement": 60.0}}`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL contain `"enrich": 20.0` (median of `[10, 20, 30]`), `"implement": 40.0` (median of `[20, 40, 60]`), and `"_total": 60.0`
