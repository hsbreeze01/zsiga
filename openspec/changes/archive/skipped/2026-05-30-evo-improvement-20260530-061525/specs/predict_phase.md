# predict_phase

## ADDED Requirements

### Requirement: _predict_phase uses regression with sufficient data

`_predict_phase` SHALL collect matching phase records from the input list, fit a linear model `y = a*x1 + b*x2 + c` where `x1 = project_lines` and `x2 = proposal_chars`, and return the predicted value clamped to `>= 0.0`.

#### Scenario: at_least_3_records_uses_regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records for phase `"explore"` with linearly related durations: `y = 0.01 * project_lines + 0.02 * proposal_chars`
- **When** `_predict_phase` is called with `project_lines=1000, proposal_chars=500`
- **Then** the result SHALL be within ±1.0 of the true linear prediction `0.01 * 1000 + 0.02 * 500 = 20.0`

#### Scenario: fewer_than_3_records_returns_median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 2 records for phase `"explore"` with durations `[10.0, 30.0]`
- **When** `_predict_phase` is called with any `project_lines` and `proposal_chars`
- **Then** it SHALL return `20.0` (the median of `[10.0, 30.0]`)

#### Scenario: zero_matching_records_returns_default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do not contain the requested phase name `"nonexistent"`
- **When** `_predict_phase` is called
- **Then** it SHALL return `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: negative_prediction_clamped_to_zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3 records for phase `"explore"` where the regression coefficients would produce a negative value for the given inputs
- **When** `_predict_phase` is called with inputs that produce a negative raw prediction
- **Then** the return value SHALL be exactly `0.0`
