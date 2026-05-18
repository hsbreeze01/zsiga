# Delta Spec: Command Timeout Tracking

## ADDED Requirements

### REQ-TT-01: Timeout Detection in Pipeline Phases

The pipeline orchestrator SHALL detect when an agent loop run returns a TIMEOUT
result (content equals `"TIMEOUT"`) for the ENRICH, IMPLEMENT, and VERIFY phases.

When a timeout is detected, the corresponding `PhaseRecord.outcome` SHALL be set
to `Outcome.TIMEOUT` instead of `Outcome.SUCCESS` or `Outcome.FAIL`.

#### Scenario: ENRICH phase times out

- Given a change is being processed with `enrich_timeout` configured
- When the enrich agent loop run returns content `"TIMEOUT"`
- Then the ENRICH PhaseRecord outcome SHALL be `timeout`
- And the change SHALL be recorded with the timeout outcome

#### Scenario: IMPLEMENT phase times out

- Given a change is in the IMPLEMENT phase with `impl_timeout` configured
- When the implement agent loop run returns content `"TIMEOUT"`
- Then the IMPLEMENT PhaseRecord outcome SHALL be `timeout`
- And mechanical verification SHALL still be attempted

#### Scenario: VERIFY phase times out

- Given a change is in the VERIFY phase with `verify_timeout` configured
- When the verify agent loop run returns content `"TIMEOUT"`
- Then the VERIFY PhaseRecord outcome SHALL be `timeout`

---

### REQ-TT-02: Per-Phase Timeout Rate Computation

The metrics collector `compute_stats()` SHALL include a `timeout_rate` field in
each phase's stats, calculated as:

```
timeout_rate = (count of phase records with outcome == "timeout") / (total phase records) * 100
```

The value SHALL be rounded to one decimal place. When a phase has zero records,
`timeout_rate` SHALL be `0`.

Additionally, a top-level `timeout_stats` dictionary SHALL be added to the stats
output containing:
- `total_timeouts`: total count of timeout outcomes across all phases
- `timeout_rate_pct`: overall timeout rate as a percentage
- `worst_phase`: the phase name with the highest timeout rate (or `""` if none)
- `phases_above_threshold`: list of phase names whose timeout rate exceeds 20%

#### Scenario: Phases with timeout records

- Given 10 implement phase records, 3 of which have outcome `"timeout"`
- When `compute_stats()` is called
- Then the implement phase stats SHALL include `timeout_rate: 30.0`
- And `timeout_stats.worst_phase` SHALL be `"implement"`
- And `timeout_stats.phases_above_threshold` SHALL include `"implement"`

#### Scenario: No timeout records

- Given 5 verify phase records, none with outcome `"timeout"`
- When `compute_stats()` is called
- Then the verify phase stats SHALL include `timeout_rate: 0.0`
- And `timeout_stats.phases_above_threshold` SHALL be empty

---

### REQ-TT-03: Timeout Rate Display in Dashboard Phase Table

The dashboard `_phase_table()` SHALL render a "Timeout Rate" column after the
"Pass Rate" column in the Phase Performance table. The value SHALL display the
`timeout_rate` percentage with a color class:
- `good` (green): timeout_rate < 10%
- `warn` (yellow): 10% ≤ timeout_rate < 20%
- `bad` (red): timeout_rate ≥ 20%

#### Scenario: Phase with 30% timeout rate

- Given the implement phase has `timeout_rate: 30.0`
- When the dashboard is rendered
- Then the implement row SHALL show `30.0%` in the Timeout Rate column
- And the value SHALL have CSS class `bad` (red)

#### Scenario: Phase with 5% timeout rate

- Given the verify phase has `timeout_rate: 5.0`
- When the dashboard is rendered
- Then the verify row SHALL show `5.0%` in the Timeout Rate column
- And the value SHALL have CSS class `good` (green)

---

### REQ-TT-04: Timeout Warning Indicator on Dashboard

When any phase's timeout rate exceeds 20%, the dashboard SHALL display a
warning banner immediately before the Phase Performance section. The warning
SHALL:
- List all phases above the 20% threshold with their timeout rates
- Use a visually distinct warning style (amber/red background, warning icon)
- Not appear when no phases exceed the threshold

#### Scenario: Two phases exceed threshold

- Given implement has `timeout_rate: 30.0` and verify has `timeout_rate: 25.0`
- When the dashboard is rendered
- Then a warning banner SHALL appear before the Phase Performance table
- And it SHALL mention both `implement (30.0%)` and `verify (25.0%)`

#### Scenario: No phases exceed threshold

- Given all phases have `timeout_rate` below 20%
- When the dashboard is rendered
- Then no warning banner SHALL appear

---

### REQ-TT-05: Timeout Summary Card

The dashboard SHALL include a summary card in the stats grid showing the overall
timeout rate (`timeout_stats.timeout_rate_pct`). The card SHALL display:
- Label: "⏱️ Timeout Rate"
- Value: the overall timeout rate percentage
- Color class: `good` / `warn` / `bad` based on the same thresholds
- Meta line: `X timeouts across N phases` where X is `total_timeouts`

#### Scenario: Dashboard with timeout history

- Given `timeout_stats.total_timeouts` is 7 and `timeout_rate_pct` is 15.0
- When the dashboard is rendered
- Then a card SHALL show "⏱️ Timeout Rate" with value `15.0%` (warn/yellow)
- And the meta line SHALL read "7 timeouts across 4 phases"
