# path-state-utils

## ADDED Requirements

### Requirement: Path resolution functions SHALL use ZSIGA_HOME env var

`_lock_path()` and `_daemon_state_path()` SHALL resolve their paths
relative to the `ZSIGA_HOME` environment variable when set, falling back
to the repository root (parent of the `zsiga` package directory) when
the variable is absent.

#### Scenario: _lock_path returns Path ending in data/lock.pid

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** ZSIGA_HOME is set to a known temporary directory
- **When** `_lock_path()` is called
- **Then** the returned Path ends with `data/lock.pid` and its parent
  directory exists on disk

#### Scenario: _lock_path creates data directory if missing

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** ZSIGA_HOME points to an empty temporary directory (no `data/` subdir)
- **When** `_lock_path()` is called
- **Then** the `data/` subdirectory SHALL be created automatically

#### Scenario: _daemon_state_path returns Path ending in data/daemon_state.json

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** ZSIGA_HOME is set to a known temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned Path ends with `data/daemon_state.json`

### Requirement: _read_daemon_state SHALL handle missing and malformed files gracefully

`_read_daemon_state()` SHALL return an empty dict when the state file
does not exist, when it contains invalid JSON, or when it is empty.

#### Scenario: _read_daemon_state returns empty dict when file absent

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** ZSIGA_HOME points to a temporary directory with no `data/daemon_state.json`
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`

#### Scenario: _read_daemon_state returns empty dict for invalid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** ZSIGA_HOME points to a directory where `data/daemon_state.json`
  contains `not-valid-json`
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`

#### Scenario: _read_daemon_state returns parsed dict for valid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** ZSIGA_HOME points to a directory where `data/daemon_state.json`
  contains `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL equal `{"pid": 123, "state": "running"}`

### Requirement: _compute_uptime_seconds SHALL return elapsed time or None

`_compute_uptime_seconds()` SHALL return a positive float (rounded to
1 decimal) when given a valid ISO-format `started_at`, and `None` when
the input is `None`, empty, or unparseable.

#### Scenario: _compute_uptime_seconds returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result SHALL be `None`

#### Scenario: _compute_uptime_seconds returns None for empty string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result SHALL be `None`

#### Scenario: _compute_uptime_seconds returns None for invalid string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result SHALL be `None`

#### Scenario: _compute_uptime_seconds returns positive float for valid ISO timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO-format timestamp from 60 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result SHALL be a float ≥ 59.0 and ≤ 61.0, rounded to 1 decimal
