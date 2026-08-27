# predict_phase

## ADDED Requirements

### Requirement: _predict_phase returns clamped regression or median fallback

The `_predict_phase` function SHALL predict a duration for a named phase. When
fewer than 3 records contain the target phase, it MUST fall back to the median
of available durations (or `DEFAULT_PHASE_SECONDS` if none exist). When 3+
records exist, it SHALL use `_fit_linear` regression and clamp the result to
`≥ 0.0`.

#### Scenario: fewer than 3 samples returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records containing the target phase with durations `[10.0, 30.0]` (2 samples)
- **When** `_predict_phase` is called
- **Then** the result SHALL be `20.0` (median of [10, 30])

#### Scenario: zero matching samples returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do NOT contain the target phase name at all
- **When** `_predict_phase` is called
- **Then** the result SHALL be `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: normal regression with 3+ samples is non-negative

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3+ records with varied `project_lines` / `proposal_chars` and phase durations forming a non-degenerate relationship
- **When** `_predict_phase` is called with reasonable input values
- **Then** the result SHALL be a non-negative float

#### Scenario: negative prediction is clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3+ records with large `project_lines` / `proposal_chars` producing a regression that would predict a negative value for tiny inputs
- **When** `_predict_phase` is called with `project_lines=1, proposal_chars=1`
- **Then** the result SHALL be `0.0` or greater (never negative)
