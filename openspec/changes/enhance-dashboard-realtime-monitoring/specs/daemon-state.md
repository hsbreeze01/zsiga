# Delta Spec: Daemon State Persistence

## ADDED Requirements

### Requirement: Daemon State File

The daemon SHALL write a `data/daemon_state.json` file on every phase transition within `daemon_loop`. The file MUST contain the following fields:

- `pid` (int): current daemon process ID
- `started_at` (ISO 8601 string): daemon start timestamp
- `cycle` (int): current cycle count (1-based)
- `state` (string): one of `running`, `paused`, `stopped`
- `current_change` (string or null): name of the change being processed, or null when idle
- `current_phase` (string or null): one of `enrich`, `implement`, `verify`, `deliver`, or null when idle
- `current_project` (string or null): target project path, or null when idle
- `last_heartbeat` (ISO 8601 string): timestamp updated every iteration of the daemon loop

#### Scenario: Daemon starts a new cycle

- **Given** the daemon is running
- **When** the daemon enters a new cycle processing change `fix-logging-bug` on project `/home/zsiga/repo`
- **Then** `data/daemon_state.json` SHALL be written with `current_change` = `"fix-logging-bug"`, `current_phase` = `"enrich"`, `current_project` = `"/home/zsiga/repo"`, and `last_heartbeat` updated to the current timestamp

#### Scenario: Daemon completes a phase transition

- **Given** the daemon is processing change `fix-logging-bug` in phase `enrich`
- **When** the phase completes and the daemon enters phase `implement`
- **Then** `data/daemon_state.json` SHALL be updated with `current_phase` = `"implement"` and `last_heartbeat` refreshed

#### Scenario: Daemon is idle between cycles

- **Given** the daemon has completed all pending changes for the current cycle
- **When** the daemon enters the idle wait period
- **Then** `data/daemon_state.json` SHALL be updated with `current_change` = null, `current_phase` = null, `state` = `"running"`, and `last_heartbeat` refreshed

#### Scenario: Daemon shuts down

- **Given** the daemon is running
- **When** the daemon loop exits (graceful shutdown)
- **Then** `data/daemon_state.json` SHALL be updated with `state` = `"stopped"`, `current_change` = null, `current_phase` = null
