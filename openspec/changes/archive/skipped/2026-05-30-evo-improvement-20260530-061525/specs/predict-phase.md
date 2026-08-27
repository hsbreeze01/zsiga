# predict-phase

## ADDED Requirements

### Requirement: _predict_phase routes between regression and median fallback

The `_predict_phase` function SHALL predict duration for a single phase. It MUST
use linear regression when ≥ 3 data points exist for the given phase, and MUST
fall back to median when fewer than 3 data points exist.

#### Scenario: sufficient records for phase triggers linear prediction

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records all containing phase `"implement"` with varying `project_lines`, `proposal_chars`, and durations
- **When** `_predict_phase` is called for phase `"implement"`
- **Then** the result SHALL be a non-negative float
- **And** the result SHALL NOT equal `DEFAULT_PHASE_SECONDS` (30.0) unless the regression output happens to be 30.0

#### Scenario: fewer than 3 records for phase uses median fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records containing phase `"explore"` with durations `[10.0, 20.0]`
- **When** `_predict_phase` is called for phase `"explore"`
- **Then** the result SHALL equal `15.0` (median of [10.0, 20.0])

#### Scenario: zero records for phase returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do NOT contain the requested phase `"nonexistent"`
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** data crafted so linear regression would predict a negative value
- **When** `_predict_phase` is called
- **Then** the result SHALL be `>= 0.0`
