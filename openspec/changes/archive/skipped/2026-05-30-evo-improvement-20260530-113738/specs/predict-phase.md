# predict-phase

## ADDED Requirements

### Requirement: _predict_phase returns regression estimate with sufficient data

When at least 3 records contain duration data for the requested phase, `_predict_phase` SHALL use linear regression (via `_fit_linear`) to produce a predicted duration, clamped to >= 0.0.

### Requirement: _predict_phase falls back to median with insufficient data

When fewer than 3 but more than 0 records contain duration data for the requested phase, `_predict_phase` SHALL return the median of the available durations.

### Requirement: _predict_phase returns DEFAULT_PHASE_SECONDS with no data

When zero records contain duration data for the requested phase, `_predict_phase` SHALL return `DEFAULT_PHASE_SECONDS` (30.0).

#### Scenario: regression path with sufficient records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records each containing phase `"implement"` with durations `[20.0, 25.0, 22.0, 30.0]` and varying `project_lines`/`proposal_chars`
- **When** `_predict_phase` is called with `project_lines=1500`, `proposal_chars=550`
- **Then** the result SHALL be a non-negative float that is NOT equal to the median of the 4 durations (i.e., regression was used, not median fallback)

#### Scenario: median fallback with fewer than 3 records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records containing phase `"explore"` with durations `[10.0, 30.0]`
- **When** `_predict_phase` is called
- **Then** the result SHALL be `20.0` (the median of `[10.0, 30.0]`)

#### Scenario: zero records returns DEFAULT_PHASE_SECONDS

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do NOT contain phase `"nonexistent"`
- **When** `_predict_phase` is called with `phase_name="nonexistent"`
- **Then** the result SHALL be `30.0` (DEFAULT_PHASE_SECONDS)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records with very large `project_lines`/`proposal_chars` values and phase durations that grow linearly, predicting with very small `project_lines`/`proposal_chars`
- **When** the regression would produce a negative value
- **Then** the result SHALL be `0.0` (clamped)
