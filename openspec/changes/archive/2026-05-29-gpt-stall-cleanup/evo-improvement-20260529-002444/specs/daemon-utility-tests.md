# daemon-utility-tests

## ADDED Requirements

### Requirement: Path utility functions SHALL produce deterministic paths

`_lock_path()` and `_daemon_state_path()` SHALL resolve to predictable
sub-paths under `ZSIGA_HOME` (or the repo root when the env var is unset).
The `data/` directory SHALL be created automatically by `_lock_path()` when it
does not exist.

#### Scenario: lock_path uses ZSIGA_HOME env var

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` under that directory
- **And** the `data/` sub-directory exists on disk

#### Scenario: lock_path falls back to repo root

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is NOT set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` under the parent of `zsiga/`

#### Scenario: daemon_state_path uses ZSIGA_HOME env var

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json` under that directory

---

### Requirement: _read_daemon_state SHALL be resilient to missing or malformed files

`_read_daemon_state()` SHALL return an empty `dict` when the state file does
not exist, contains invalid JSON, or cannot be read due to an OS error.

#### Scenario: read_daemon_state with no file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: read_daemon_state with valid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{"pid": 42, "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 42, "cycle": 5}`

#### Scenario: read_daemon_state with malformed JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{invalid json!!!`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

---

### Requirement: _compute_uptime_seconds SHALL return elapsed time or None

`_compute_uptime_seconds()` SHALL return a positive float rounded to one
decimal when given a valid ISO timestamp, and `None` when the input is missing
or unparseable.

#### Scenario: uptime with None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** it returns `None`

#### Scenario: uptime with invalid string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** it returns `None`

#### Scenario: uptime with valid recent timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is set to 10 seconds ago in ISO format
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` ≥ 9.0 and ≤ 12.0
- **And** the result has at most one decimal place

---

### Requirement: _health_check SHALL probe the SQLite database

`_health_check()` SHALL return a dict with `"status": "healthy"` and a
`"db_records"` count on success, or `"status": "unhealthy"` with an error
message on failure.

#### Scenario: health check against valid database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** it returns `{"status": "healthy", "db_records": 3}`

#### Scenario: health check against non-existent database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a file that does not exist
- **When** `_health_check(db_path)` is called
- **Then** it returns a dict with `"status": "unhealthy"` and a non-empty `"error"`
