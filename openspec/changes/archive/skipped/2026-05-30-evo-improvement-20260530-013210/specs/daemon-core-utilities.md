# daemon-core-utilities

Delta spec for core utility classes and functions in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: DaemonState class provides shared mutable signal state

The system SHALL provide a `DaemonState` class with class-level
attributes `paused` (default `False`) and `shutdown` (default `False`).
These attributes MUST be mutable at the class level so signal handlers
can toggle them.

#### Scenario: DaemonState has correct defaults

- **testable**: true
- **target**: zsiga/daemon.py::DaemonState
- **Given** a fresh `DaemonState` instance
- **When** attributes are inspected
- **Then** `paused` is `False` and `shutdown` is `False`

#### Scenario: DaemonState attributes are mutable

- **testable**: true
- **target**: zsiga/daemon.py::DaemonState
- **Given** a `DaemonState` instance
- **When** `paused` is set to `True`
- **Then** `instance.paused` is `True`

### Requirement: _compute_uptime_seconds computes elapsed time

The system SHALL provide `_compute_uptime_seconds(started_at)` that
parses an ISO-format timestamp and returns elapsed seconds rounded to
1 decimal. It MUST return `None` when input is `None`, empty, or
unparseable.

#### Scenario: _compute_uptime_seconds returns positive elapsed time

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an ISO timestamp 60 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a positive float ≥ 59.0

#### Scenario: _compute_uptime_seconds returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: _compute_uptime_seconds returns None for invalid input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

### Requirement: _health_check probes database liveness

The system SHALL provide `_health_check(db_path)` that connects to a
SQLite database, queries `SELECT COUNT(*) FROM changes`, and returns
`{"status": "healthy", "db_records": <int>}`. On any failure it MUST
return `{"status": "unhealthy", "error": "<message>"}`.

#### Scenario: _health_check returns healthy for valid database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "healthy", "db_records": 3}`

#### Scenario: _health_check returns unhealthy for missing database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a non-existent file
- **When** `_health_check(db_path)` is called
- **Then** the result `["status"]` is `"unhealthy"`
