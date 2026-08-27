# daemon-status-response

## ADDED Requirements

### Requirement: _build_status_json SHALL return valid JSON with daemon and queue keys

`_build_status_json()` SHALL produce a JSON string with top-level keys
`"daemon"` and `"queue"`.

#### Scenario: status json structure with mocked state

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` is mocked to return `{"pid": 42, "state": "running", "cycle": 1}` and `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_status_json()` is called
- **Then** the result SHALL be a valid JSON string; when parsed, `parsed["daemon"]["pid"]` SHALL equal `42` and `parsed["daemon"]["state"]` SHALL equal `"running"` and `"queue"` SHALL be an empty list

#### Scenario: status json includes uptime from started_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` is mocked to return `{"pid": 1, "state": "running", "started_at": "2025-01-01T00:00:00"}` and `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_status_json()` is called
- **Then** the parsed result SHALL contain `parsed["daemon"]["uptime_seconds"]` as a number (or `None`)

---

### Requirement: _build_current_json SHALL return JSON with phase progress

`_build_current_json()` SHALL produce a JSON string with top-level keys
`"daemon"`, `"current"`, and `"queue"`.

#### Scenario: current json includes phase progress array

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state` is mocked to return `{"pid": 1, "state": "running", "cycle": 3, "current_phase": "IMPLEMENT", "started_at": "2025-01-01T00:00:00"}` and `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_current_json()` is called
- **Then** the parsed result SHALL contain `parsed["current"]["phase_progress"]` as a list of 6 items where one item has `status == "active"` and `name == "IMPLEMENT"`

---

### Requirement: _health_check SHALL probe SQLite liveness

`_health_check(db_path)` SHALL connect to the given SQLite database,
count rows in `changes`, and return a status dict.

#### Scenario: healthy database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** it SHALL return `{"status": "healthy", "db_records": 3}`

#### Scenario: missing database returns unhealthy

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a `db_path` that does not exist on disk
- **When** `_health_check(db_path)` is called
- **Then** it SHALL return a dict with `"status" == "unhealthy"`

---

### Requirement: _build_metrics_json SHALL return JSON with summary or error

`_build_metrics_json()` SHALL return a JSON string. On success it
contains `"summary"` and `"phases"` keys; on failure it contains an
`"error"` key.

#### Scenario: metrics json returns error on compute_stats failure

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` raises an exception when called
- **When** `_build_metrics_json()` is called
- **Then** the parsed result SHALL contain an `"error"` key with a non-empty string value
