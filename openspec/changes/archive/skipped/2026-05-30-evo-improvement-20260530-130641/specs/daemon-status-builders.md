# daemon-status-builders

Delta spec for testing status/metrics JSON builder functions in
`zsiga/daemon.py` that have no direct test coverage.

## ADDED Requirements

### Requirement: Status JSON construction

`_build_status_json()` SHALL read daemon state and scan the proposal
queue, then return a JSON string containing `daemon` and `queue`
top-level keys. The `daemon` object SHALL include `uptime_seconds`
computed from the stored `started_at`.

#### Scenario: Happy path with daemon state and queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"pid": 1, "state": "running", "cycle": 5, "started_at": "<60s ago>", "last_heartbeat": "2025-01-01T00:00:00"}`
- **And** `_scan_proposal_queue` returns `[{"name": "p1", "project": "zsiga", "summary": "fix", "phase": "ENRICH", "lifecycle": "active", "paused": false, "paused_reason": "", "consecutive_fails": 0}]`
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON with keys `daemon` and `queue`
- **And** `daemon.uptime_seconds` is a number near 60
- **And** `queue` has length 1

#### Scenario: Empty daemon state returns defaults

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{}` and `_scan_proposal_queue` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the parsed JSON has `daemon.state` equal to `"unknown"`
- **And** `queue` is an empty list

---

### Requirement: Metrics JSON construction

`_build_metrics_json()` SHALL return a JSON string with `summary`,
`phases`, and `rolling_rates` keys on success. On any exception it
SHALL return a JSON string with an `error` key.

#### Scenario: Metrics available

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `metrics.dashboard.compute_stats` returns `{"summary": {"total": 10}, "phases": {"CLARIFY": 3}}`
- **When** `_build_metrics_json()` is called
- **Then** the parsed JSON has keys `summary`, `phases`, `rolling_rates`

#### Scenario: Metrics module raises exception

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `metrics.dashboard.compute_stats` raises `RuntimeError("db locked")`
- **When** `_build_metrics_json()` is called
- **Then** the parsed JSON has key `error` with value containing `"db locked"`

---

### Requirement: Health check

`_health_check(db_path)` SHALL connect to the given SQLite database,
count rows in the `changes` table, and return a dict with
`status: "healthy"` and `db_records: <count>`. On failure it SHALL
return `status: "unhealthy"` with an `error` message.

#### Scenario: Healthy database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database with a `changes` table containing 5 rows
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "healthy", "db_records": 5}`

#### Scenario: Nonexistent database file

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a nonexistent file
- **When** `_health_check(db_path)` is called
- **Then** the result has `status: "unhealthy"`
- **And** the result has an `error` key
