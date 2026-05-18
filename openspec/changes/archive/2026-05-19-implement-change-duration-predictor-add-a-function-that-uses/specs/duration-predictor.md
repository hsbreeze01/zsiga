# Delta Spec: Change Duration Predictor

## ADDED Requirements

### Requirement: predict_change_duration
The system SHALL provide a function `predict_change_duration(phase_stats, project_lines, proposal_chars)` that estimates the duration (in seconds) of each pipeline phase for a proposed change.

#### Scenario: Predict with sufficient historical data
- Given a `phase_stats` list containing at least 3 historical change records, each record having `phases` (dict of phase_name → duration_seconds), `project_lines` (int), and `proposal_chars` (int)
- And `project_lines` is a positive integer representing the target project size
- And `proposal_chars` is a positive integer representing the proposal text length
- When `predict_change_duration` is called
- Then the function SHALL return a dict mapping each known phase name to an estimated duration in seconds (float)
- And each estimated duration SHALL be a non-negative number

#### Scenario: Predict with insufficient historical data
- Given a `phase_stats` list with fewer than 3 records
- When `predict_change_duration` is called
- Then the function SHALL return a dict of default fallback estimates per phase
- And the fallback estimates SHALL be the median duration of available records per phase, or a hardcoded default of 30.0 seconds if no data exists for a given phase

### Requirement: duration estimation algorithm
The estimation algorithm SHALL use a linear model that correlates `project_lines` and `proposal_chars` with per-phase durations from historical data.

#### Scenario: Linear regression per phase
- Given at least 3 historical records with known phase durations
- When the estimator computes per-phase predictions
- Then it SHALL fit a simple linear model per phase: `duration = a * project_lines + b * proposal_chars + c`
- And it SHALL predict using the fitted model with the new change's `project_lines` and `proposal_chars`

#### Scenario: Prediction clamping
- When a predicted duration for any phase is negative
- Then the system SHALL clamp it to 0.0 seconds

### Requirement: phase_stats data format
The `phase_stats` parameter SHALL be a list of dicts, where each dict conforms to the following structure:

```
{
  "project_lines": int,       # LOC of the project at change time
  "proposal_chars": int,      # character count of the proposal
  "phases": {
    "explore": float,         # duration in seconds
    "design": float,
    "implement": float,
    "verify": float,
    "deliver": float
  }
}
```

#### Scenario: Missing phase keys in historical records
- Given some historical records lack certain phase keys
- When the estimator processes phase_stats
- Then it SHALL skip missing phases for that record without error
- And it SHALL still produce estimates for phases that have sufficient data

### Requirement: total estimated runtime
The function SHALL also include a `"_total"` key in the returned dict whose value is the sum of all per-phase estimates.

#### Scenario: Total runtime calculation
- Given predicted durations for phases explore=10.0, design=5.0, implement=20.0, verify=8.0, deliver=3.0
- When the result dict is returned
- Then the `"_total"` key SHALL have value 46.0

### Requirement: predictor module location
The duration predictor SHALL reside in the `zsiga` package as a self-contained module named `duration_predictor`.

#### Scenario: Import path
- Given the zsiga package is installed
- When a user writes `from zsiga.duration_predictor import predict_change_duration`
- Then the import SHALL succeed without error
