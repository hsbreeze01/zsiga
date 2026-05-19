# Delta Spec: Dashboard Daemon Status Card

## ADDED Requirements

### Requirement: Daemon Status Card Rendering

The dashboard generator SHALL render a Daemon Status Card section in the HTML output, positioned below the hero area and above the existing metric cards. The card MUST display the following fields read from `data/daemon_state.json`:

- **PID**: the daemon process ID
- **Started At**: daemon start time formatted via `_fmt_seconds` or equivalent human-readable format
- **Cycle**: current cycle count
- **Processing**: the `current_change` value, or "Idle — Next cycle in Xh" when idle (X estimated from heartbeat age vs. configured cycle interval)
- **State**: `running` / `paused` / `stopped`, rendered as a color-coded badge (`good` / `warn` / `bad`)
- **Dashboard URL**: the URL from which the dashboard is accessed

When `data/daemon_state.json` does not exist or is unreadable, the card SHALL display a "Daemon Offline" badge with state `stopped` and all fields set to "—".

#### Scenario: Daemon is actively processing a change

- **Given** `data/daemon_state.json` exists with `state` = `"running"` and `current_change` = `"add-retry-logic"`
- **When** the dashboard HTML is generated
- **Then** the Daemon Status Card SHALL display PID, Started At, Cycle, Processing = `"add-retry-logic"`, State badge with class `good` showing "running", and the dashboard URL

#### Scenario: Daemon is idle

- **Given** `data/daemon_state.json` exists with `state` = `"running"` and `current_change` = null and `last_heartbeat` = 30 minutes ago with a 1-hour cycle interval
- **When** the dashboard HTML is generated
- **Then** the Processing field SHALL display `"Idle — Next cycle in ~30m"`

#### Scenario: Daemon state file is missing

- **Given** `data/daemon_state.json` does not exist
- **When** the dashboard HTML is generated
- **Then** the Daemon Status Card SHALL display a `bad`-colored "Daemon Offline" badge and "—" for PID, Started At, Cycle, and Processing
