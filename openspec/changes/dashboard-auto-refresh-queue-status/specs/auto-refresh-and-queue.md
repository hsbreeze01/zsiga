# Spec: Dashboard Auto-Refresh & Queue/Stage Real-Time Display

## ADDED Requirements

### Requirement: JavaScript-Based Periodic Data Refresh

The dashboard SHALL replace the `<meta http-equiv="refresh">` whole-page reload with a JavaScript `fetch`-based polling mechanism that updates only the dynamic regions of the page.

#### Scenario: Periodic fetch replaces meta-refresh

- **Given** the dashboard HTML is loaded in a browser
- **When** the page finishes loading
- **Then** the `<meta http-equiv="refresh">` tag SHALL NOT be present
- **And** a JavaScript `setInterval` SHALL fetch status data every 600 seconds (10 minutes)
- **And** only the daemon status, proposal queue, and current phase sections SHALL be updated in the DOM
- **And** the rest of the page (static content, CSS, layout) SHALL remain unchanged

#### Scenario: Fetch failure falls back to static content

- **Given** the dashboard HTML is loaded and static snapshot data is rendered server-side
- **When** the JavaScript fetch to `/api/status.json` fails (network error, server unavailable)
- **Then** the existing static content SHALL remain visible and functional
- **And** a subtle error indicator SHALL be shown near the refresh timestamp

---

### Requirement: Daemon Status JSON API

The daemon SHALL expose an HTTP endpoint that returns the current daemon state and proposal queue as a JSON document.

#### Scenario: API returns daemon state and queue

- **Given** the daemon is running with an active HTTP handler
- **When** a GET request is made to `/api/status.json`
- **Then** the response SHALL have `Content-Type: application/json`
- **And** the JSON body SHALL contain a `daemon` object with fields: `pid`, `state`, `cycle`, `current_change`, `current_phase`, `current_project`, `heartbeat`
- **And** the JSON body SHALL contain a `queue` array of objects, each with: `name`, `project`, `summary`
- **And** the `queue` array SHALL reflect a real-time scan of `openspec/changes/` directories (or a low-cost cache)

#### Scenario: API handles missing daemon state gracefully

- **Given** `daemon_state.json` does not exist or is malformed
- **When** a GET request is made to `/api/status.json`
- **Then** the API SHALL return sensible defaults (e.g., `state: "unknown"`, empty `queue`)
- **And** the response HTTP status SHALL still be 200

---

### Requirement: Proposal Queue Display

The dashboard SHALL display the current proposal queue as a dynamic table with visual indicators for the active proposal.

#### Scenario: Queue table renders proposal entries

- **Given** the `/api/status.json` endpoint returns a non-empty `queue` array
- **When** the dashboard JavaScript processes the response
- **Then** a table SHALL be rendered with columns: index, proposal name, project, summary
- **And** the summary SHALL be derived from the first heading line of each proposal's `proposal.md`

#### Scenario: Active proposal is visually highlighted

- **Given** the `daemon.current_change` in the API response matches a queue entry
- **When** the queue table is rendered
- **Then** the matching row SHALL have a distinct visual highlight (e.g., yellow left border)
- **And** a phase badge SHALL be displayed on that row showing the current phase name (enrich / implement / review / verify / deliver)

#### Scenario: Empty queue display

- **Given** the `/api/status.json` endpoint returns an empty `queue` array
- **When** the dashboard JavaScript processes the response
- **Then** the queue section SHALL display "Queue empty — idle polling"

---

### Requirement: Refresh Timestamp Indicator

The dashboard SHALL display the time of the last successful data refresh and a countdown to the next refresh.

#### Scenario: Last-refreshed timestamp shown

- **Given** the dashboard has completed at least one successful fetch
- **When** the DOM is updated with new data
- **Then** a "Last refreshed: HH:MM:SS" indicator SHALL be displayed in the top-right area of the dashboard
- **And** a countdown timer (in minutes) to the next refresh SHALL be shown alongside it

---

## MODIFIED Requirements

### Requirement: Daemon phase state updates

The daemon SHALL write `current_change` and `current_phase` to `daemon_state.json` each time it enters a new pipeline phase, ensuring the API reflects the latest state.

#### Scenario: Phase transition updates state file

- **Given** the daemon is processing a change and transitions from one phase to the next
- **When** the new phase begins
- **Then** `daemon_state.json` SHALL be updated with the new `current_phase` value before proceeding with phase logic

---

### Requirement: Static dashboard generation preserved

The `generate_dashboard()` function SHALL continue to produce a complete static HTML file with embedded snapshot data, serving as the initial load and non-JS fallback.

#### Scenario: Static HTML remains self-contained

- **Given** `generate_dashboard()` is called (e.g., after a daemon cycle)
- **When** the output HTML file is written
- **Then** it SHALL contain all current data rendered inline (same as today)
- **And** it SHALL also include the JavaScript polling code that overlays dynamic updates on top of the static content
