# Delta Spec: Dashboard Realtime Monitoring Fix

## ADDED Requirements

### Requirement: Daemon Real-Time Status Display

The dashboard SHALL read `data/daemon_state.json` and render a Daemon status card row
between the hero area and the metrics card grid.

#### Scenario: Daemon is actively running a change

- **Given** `data/daemon_state.json` exists and contains `state: "running"` with a non-empty `current_change`
- **When** the dashboard is rendered
- **Then** the Daemon status card SHALL display:
  - PID value from `pid` field
  - Started-at timestamp from `started_at` field
  - Current cycle number from `cycle` field
  - State badge showing "running" with appropriate styling
  - Processing label showing the `current_change` name and `current_phase`
  - Last heartbeat timestamp from `last_heartbeat` field

#### Scenario: Daemon is idle / resting

- **Given** `data/daemon_state.json` exists and contains `state: "resting"` or `current_change` is empty/null
- **When** the dashboard is rendered
- **Then** the Processing label SHALL display "Idle"

#### Scenario: Daemon state file is missing or unreadable

- **Given** `data/daemon_state.json` does not exist or cannot be parsed
- **When** the dashboard is rendered
- **Then** the Daemon status card SHALL display "Daemon offline" without raising an error

---

### Requirement: Failure Diagnosis Panel

The dashboard SHALL display a "Failure Diagnosis" panel after the Phase Performance table
and before the Resource Usage section.

#### Scenario: Recent failures exist in learnings and changes

- **Given** `data/learnings.jsonl` contains entries with `pipeline.fail.*` or `code.*` patterns
- **And** there are changes with `outcome=reverted` or failed verify/review status
- **When** the dashboard is rendered
- **Then** the panel SHALL display up to 10 most recent failures, each showing:
  - Change name
  - Project name
  - Failed phase
  - Latest matching lesson takeaway from learnings.jsonl
  - Duration
  - Timestamp
- **And** each entry SHALL be rendered as an HTML `<details>/<summary>` element for expand/collapse

#### Scenario: A failed change has a diagnosis file

- **Given** a failed change has a non-empty `openspec/changes/{name}/diagnosis.md` file
- **When** that failure entry is expanded
- **Then** the diagnosis content SHALL be rendered inside the details element

#### Scenario: No failures exist

- **Given** there are no reverted or failed changes
- **When** the dashboard is rendered
- **Then** the panel SHALL display "No failures recorded" placeholder text

---

### Requirement: Sparkline Trend Rendering

The dashboard SHALL render success-rate and duration trend visualizations
in the Resource Usage area.

#### Scenario: Success trend with sufficient data

- **Given** there are at least 2 completed changes with outcome data
- **When** the dashboard is rendered
- **Then** a "Success Trend" card SHALL display a sparkline chart of the rolling success rate
  for the most recent 20 changes
- **And** the sparkline SHALL be rendered using `_sparkline_html` with data from `compute_rolling_rates`

#### Scenario: Duration trend with sufficient data

- **Given** there are at least 2 completed changes with duration data
- **When** the dashboard is rendered
- **Then** a "Duration Trend" card SHALL display a bar chart of the most recent 20 changes' durations
- **And** each bar SHALL be color-coded: green for success, red for failure
- **And** bar heights SHALL represent duration as a percentage of the maximum duration in the set

#### Scenario: Insufficient data for trends

- **Given** fewer than 2 changes have been completed
- **When** the dashboard is rendered
- **Then** the trend cards SHALL display "Insufficient data" placeholder text

---

### Requirement: Dashboard Auto-Refresh

The dashboard HTML output SHALL include auto-refresh metadata so the page
reloads periodically without user interaction.

#### Scenario: Dashboard page is opened in a browser

- **Given** the dashboard has been rendered to `site/dashboard.html`
- **When** a user opens the page in a browser
- **Then** the `<head>` section SHALL contain `<meta http-equiv="refresh" content="60">`
- **And** a visible text hint "Auto-refresh: 60s" SHALL appear at the top of the page body

#### Scenario: Auto-refresh hint visibility

- **Given** the dashboard page is rendered
- **When** the user views the page
- **Then** the auto-refresh hint text SHALL use subdued styling (small font, muted color) so it does not dominate the layout
