# Delta Spec: Dashboard Render Function Wiring

## MODIFIED Requirements

### Requirement: Dashboard rendering SHALL integrate daemon status section

The `_render()` function in `dashboard.py` SHALL call `_daemon_status_section()` and include the returned HTML between the hero div and the metrics grid (`<div class="grid">`). This ensures the daemon's current state (working/resting) is visible on the dashboard without any new function creation.

#### Scenario: Daemon status card appears on generated dashboard
- **Given** `data/daemon_state.json` exists with valid daemon state
- **When** `generate_dashboard()` is called
- **Then** the output HTML SHALL contain the daemon status section HTML between the hero area and the metrics grid

#### Scenario: Graceful handling when daemon state is unavailable
- **Given** `data/daemon_state.json` does not exist or is malformed
- **When** `_daemon_status_section()` is called within `_render()`
- **Then** `_render()` SHALL NOT raise an exception; the section SHALL be empty or show a fallback message

---

### Requirement: Dashboard rendering SHALL integrate failure diagnosis section

The `_render()` function SHALL call `_failure_diagnosis_section()` and include the returned HTML between the Phase Performance section and the Resource Usage section. This surfaces recent failure learnings and diagnosis data on the dashboard.

#### Scenario: Failure diagnosis panel appears on generated dashboard
- **Given** there is at least one failed change in the changes directory with associated learnings
- **When** `generate_dashboard()` is called
- **Then** the output HTML SHALL contain the failure diagnosis section between Phase Performance and Resource Usage

#### Scenario: No failures to display
- **Given** there are no failed changes in the changes directory
- **When** `generate_dashboard()` is called
- **Then** the failure diagnosis section SHALL render as empty or with a "no failures" indicator, and SHALL NOT cause an error

---

### Requirement: Dashboard rendering SHALL integrate sparkline trend visualization

The `_render()` function SHALL call `compute_rolling_rates()` from `collector` module, pass the result to `_sparkline_html()`, and include the rendered sparkline in a card within the dashboard. This provides a visual rolling success-rate trend.

#### Scenario: Sparkline card appears on generated dashboard
- **Given** `compute_rolling_rates()` returns a non-empty list of rate data points
- **When** `generate_dashboard()` is called
- **Then** the output HTML SHALL contain an inline SVG or visual sparkline element showing the rolling rate trend

#### Scenario: Insufficient data for sparkline
- **Given** `compute_rolling_rates()` returns an empty list or None
- **When** `_render()` processes the sparkline
- **Then** the dashboard SHALL render without error; the sparkline area MAY show "insufficient data"

---

### Requirement: Dashboard page SHALL include auto-refresh metadata

The `_render()` function's returned HTML SHALL include a `<meta http-equiv="refresh" content="60">` tag in the `<head>` section, and a small visible indicator at the top of `<body>` stating the auto-refresh interval.

#### Scenario: Auto-refresh meta tag present
- **Given** `_render()` generates the full dashboard HTML
- **When** the HTML is inspected
- **Then** the `<head>` SHALL contain `<meta http-equiv="refresh" content="60">`
- **And** the `<body>` SHALL start with a right-aligned div showing "Auto-refresh: 60s"

---

### Requirement: No new functions SHALL be introduced

All changes SHALL be confined to the `_render()` function body — variable assignments and f-string insertions only. No new function definitions, no modifications to other modules, and no changes to `collector.py` or daemon state writing logic.

#### Scenario: Diff scope is limited
- **Given** the change is implemented
- **When** the diff is reviewed
- **Then** only `_render()` function in `dashboard.py` SHALL show modifications
- **And** no new function definitions SHALL appear in the diff
