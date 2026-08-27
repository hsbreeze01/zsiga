# predict-change-duration-edges

## ADDED Requirements

### Requirement: predict_change_duration switches between regression and fallback

The public entry point `predict_change_duration` SHALL use regression-based
prediction when `len(phase_stats) >= 3` and SHALL delegate to `_fallback_estimates`
when `len(phase_stats) < 3`.

#### Scenario: exactly 3 records triggers regression path

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** exactly 3 records with diverse `project_lines`/`proposal_chars`
- **When** `predict_change_duration` is called
- **Then** the result SHALL contain all known phase names as keys
- **And** each value SHALL be a non-negative float
- **And** `"_total"` SHALL equal the sum of per-phase estimates

#### Scenario: records with heterogeneous phase coverage

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 3 records where each covers a different subset of phases (record 1: explore+design, record 2: design+implement, record 3: implement+verify)
- **When** `predict_change_duration` is called
- **Then** all 4 phases (explore, design, implement, verify) SHALL appear in the result
- **And** phases with only 1-2 data points in the regression set SHALL still produce estimates (via median fallback in `_predict_phase`)

#### Scenario: _total is consistent with per-phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** any non-empty phase_stats list with ≥ 3 records
- **When** `predict_change_duration` is called
- **Then** `result["_total"]` SHALL equal `sum(v for k, v in result.items() if k != "_total")`
