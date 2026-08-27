# daemon-status-builders

## ADDED Requirements

### Requirement: Compute uptime seconds

`_compute_uptime_seconds(started_at)` SHALL compute elapsed seconds since the
given ISO-format timestamp, rounded to one decimal place.  When `started_at`
is `None`, empty, or unparseable, it SHALL return `None`.

#### Scenario: Valid ISO timestamp returns positive float

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an ISO-format string 60 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is approximately `60.0` (±5 seconds) and is rounded to 1 decimal place

#### Scenario: None input returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: Empty string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: Invalid string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

---

### Requirement: Build status JSON

`_build_status_json()` SHALL return a JSON string with top-level keys
`"daemon"` and `"queue"`.  The `"daemon"` object SHALL contain keys `"pid"`,
`"state"`, `"uptime_seconds"`, `"current_change"`, `"current_phase"`.

#### Scenario: Returns valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"pid": 42, "state": "running", "started_at": "<recent ISO>", "cycle": 1}` and `_scan_proposal_queue` returns `[]`
- **When** `_build_status_json()` is called (with both helpers mocked)
- **Then** the result parses as JSON and contains `"daemon"` and `"queue"` keys; `daemon.state` equals `"running"`

---

### Requirement: Build metrics JSON

`_build_metrics_json()` SHALL return a JSON string.  When
`compute_stats()` succeeds it SHALL contain `"summary"` and `"phases"`.  When
an exception occurs it SHALL return `{"error": "<message>"}`.

#### Scenario: Successful metrics build

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` returns `{"summary": {"total": 5}, "phases": {}}`
- **When** `_build_metrics_json()` is called (with `compute_stats` mocked)
- **Then** the result parses as JSON containing `"summary"` with `"total": 5`

#### Scenario: Metrics build on exception returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` raises `RuntimeError("db unavailable")`
- **When** `_build_metrics_json()` is called (with `compute_stats` mocked)
- **Then** the result parses as JSON containing `"error": "db unavailable"`

---

### Requirement: Build current JSON

`_build_current_json()` SHALL return a JSON string with top-level keys
`"daemon"`, `"current"`, `"queue"`.  The `"current"` object SHALL contain a
`"phase_progress"` list where each entry has `"name"` and `"status"`.

#### Scenario: Returns valid JSON with phase_progress

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state` returns `{"pid": 1, "state": "running", "current_phase": "IMPLEMENT", "started_at": "<ISO>"}` and `_scan_proposal_queue` returns `[]`
- **When** `_build_current_json()` is called (with both helpers mocked)
- **Then** the result parses as JSON; `current.phase_progress` is a list; the entry with `"name": "IMPLEMENT"` has `"status": "active"`

---

### Requirement: Health check against SQLite database

`_health_check(db_path)` SHALL query the `changes` table and return
`{"status": "healthy", "db_records": <int>}` on success.  On any failure it
SHALL return `{"status": "unhealthy", "error": "<message>"}`.

#### Scenario: Healthy database returns record count

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** it returns `{"status": "healthy", "db_records": 3}`

#### Scenario: Missing database returns unhealthy

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a non-existent file
- **When** `_health_check(db_path)` is called
- **Then** it returns a dict with `"status": "unhealthy"` and a non-empty `"error"` string
