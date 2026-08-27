# daemon-status-builders

## ADDED Requirements

### REQ-SB-01: Status JSON builder

`_build_status_json` SHALL compose a JSON string with top-level keys `"daemon"`
and `"queue"`. The `"daemon"` object SHALL contain at minimum keys: `pid`, `state`,
`cycle`, `current_change`, `current_phase`, `current_project`, `heartbeat`,
`uptime_seconds`. The `"queue"` value SHALL be the output of `_scan_proposal_queue`.

#### Scenario: status-json-structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** an empty daemon state and a changes directory with at least one proposal
- **When** `_build_status_json()` is called
- **Then** the result is valid JSON parseable to a dict with keys `"daemon"` and
  `"queue"`, where `"daemon"` has keys `pid`, `state`, `cycle`, `uptime_seconds`

#### Scenario: status-json-default-unknown-state

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** no `daemon_state.json` file exists (empty state)
- **When** `_build_status_json()` is called
- **Then** the parsed `daemon.state` is `"unknown"` (the default)

### REQ-SB-02: Metrics JSON builder

`_build_metrics_json` SHALL return a JSON string. When `compute_stats()` succeeds,
the result SHALL contain `"summary"` and `"phases"` keys. When it raises an
exception, the result SHALL contain an `"error"` key with the exception message.

#### Scenario: metrics-json-on-compute-error

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` raises `ImportError("no module")`
- **When** `_build_metrics_json()` is called
- **Then** returns a JSON string parseable to `{"error": "no module"}`

### REQ-SB-03: Current JSON builder with phase progress

`_build_current_json` SHALL return a JSON string with top-level keys `"daemon"`,
`"current"`, and `"queue"`. The `"current"` object SHALL contain `"phase_progress"`,
an array of phase objects each with `"name"` and `"status"`. Phases before the
current phase SHALL have status `"done"`, the current phase SHALL have status
`"active"`, and phases after SHALL have status `"pending"`.

#### Scenario: current-json-phase-progress

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** daemon state with `current_phase="IMPLEMENT"` and no other state
- **When** `_build_current_json()` is called
- **Then** the parsed `current.phase_progress` is a list where CLARIFY and ENRICH
  have status `"done"`, IMPLEMENT has status `"active"`, and all subsequent phases
  have status `"pending"`

### REQ-SB-04: Health check

`_health_check` SHALL accept a database path and return a dict with `"status"`
either `"healthy"` or `"unhealthy"`. On success it SHALL include `"db_records"`
with the row count. On failure it SHALL include `"error"` with the exception message.

#### Scenario: health-check-healthy-db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database file with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** returns `{"status": "healthy", "db_records": 3}`

#### Scenario: health-check-missing-db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a path to a non-existent database file
- **When** `_health_check(db_path)` is called
- **Then** returns a dict with `"status": "unhealthy"` and an `"error"` key
