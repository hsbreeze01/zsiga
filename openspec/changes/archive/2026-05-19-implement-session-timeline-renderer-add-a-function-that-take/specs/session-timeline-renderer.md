# Spec: Session Timeline Renderer

## ADDED Requirements

### REQ-TL-01: ASCII Timeline Rendering from Session JSON

The system SHALL provide a function `render_timeline(session: dict) -> str` that accepts a session summary dict (as produced by `export_session`) and returns a multi-line ASCII string representing a visual timeline of the session's phases.

#### Scenario: Render a session with multiple phases

- **Given** a session dict with `change_name="add-health-endpoint"`, `outcome="success"`, `started_at="2026-05-15T14:00:00"`, `finished_at="2026-05-15T14:05:00"`, `total_runtime_seconds=300.0`, and phases:
  - enrich: seconds_used=45.0, outcome=success
  - implement: seconds_used=150.0, outcome=success
  - verify: seconds_used=60.0, outcome=success
  - deliver: seconds_used=45.0, outcome=success
- **When** `render_timeline(session)` is called
- **Then** the returned string SHALL contain:
  - A header line with the change name and overall outcome
  - One row per phase showing: phase name, a proportional Unicode block-character duration bar, the duration in seconds, and the phase outcome
  - A footer line with total runtime and the session time range

#### Scenario: Render a session with a single phase

- **Given** a session dict with one phase (implement, seconds_used=120.0)
- **When** `render_timeline(session)` is called
- **Then** the output SHALL show exactly one phase row with a full-width bar and the total runtime in the footer

#### Scenario: Render a session with zero phases

- **Given** a session dict with an empty `phases` list
- **When** `render_timeline(session)` is called
- **Then** the output SHALL show the header and a "no phases recorded" message, with no phase rows

### REQ-TL-02: Proportional Duration Bars

Each phase's duration bar SHALL be proportional to `seconds_used` relative to `total_runtime_seconds`. The bar width SHALL use Unicode block characters (`█` for filled, `░` for empty) with a maximum width of 40 characters.

#### Scenario: Proportional bars for varying durations

- **Given** a session with total_runtime_seconds=200 and phases:
  - enrich: seconds_used=50 (25%)
  - implement: seconds_used=100 (50%)
  - verify: seconds_used=30 (15%)
  - deliver: seconds_used=20 (10%)
- **When** the timeline is rendered
- **Then** the enrich bar SHALL be approximately 10 `█` characters wide (25% of 40)
- **And** the implement bar SHALL be approximately 20 `█` characters wide (50% of 40)

#### Scenario: Zero total runtime

- **Given** a session with `total_runtime_seconds=0` and phases with `seconds_used=0`
- **When** the timeline is rendered
- **Then** all phase bars SHALL be zero-width (no filled characters)

### REQ-TL-03: Phase Outcome Indicators

Each phase row SHALL display a visual indicator of the phase outcome:
- `✓` for `success`
- `✗` for `fail`
- `⏱` for `timeout`
- `↩` for `reverted`
- `–` for `skipped` or unknown

#### Scenario: Failed phase indicator

- **Given** a session with an implement phase where `outcome="fail"`
- **When** the timeline is rendered
- **Then** the implement row SHALL show `✗` as the outcome indicator

### REQ-TL-04: CLI-Compatible Output

The returned string SHALL be pure ASCII/Unicode text with no ANSI escape codes, suitable for:
- Terminal console output
- Embedding in log files
- Rendering in the dashboard HTML within a `<pre>` block

#### Scenario: No ANSI codes in output

- **Given** any valid session dict
- **When** `render_timeline(session)` is called
- **Then** the output SHALL NOT contain any ANSI escape sequences (bytes 0x1b)

### REQ-TL-05: Session Time Range Display

The footer of the timeline SHALL display the session's start time, end time, and total runtime formatted for human readability.

#### Scenario: Time range formatting

- **Given** a session with `started_at="2026-05-15T14:00:00"` and `finished_at="2026-05-15T14:05:18"`
- **When** the timeline is rendered
- **Then** the footer SHALL contain both timestamps and the total runtime formatted as `5m 18s` (or similar human-readable format)
