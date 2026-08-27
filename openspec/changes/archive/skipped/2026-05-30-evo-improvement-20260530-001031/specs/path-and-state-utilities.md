# Delta Spec: Path and State Utility Functions

## ADDED Requirements

### Requirement: lock-path-resolution

The system SHALL provide `_lock_path()` that resolves the PID lock file path
using `ZSIGA_HOME` environment variable (falling back to repo root) and ensures
the `data/` directory exists.

#### Scenario: returns-data-lock-pid-under-zsiga-home

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid`
- **And** the `data/` directory exists on disk

#### Scenario: creates-data-dir-if-missing

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** `ZSIGA_HOME` points to a directory where `data/` does not exist
- **When** `_lock_path()` is called
- **Then** `data/` directory is created (parents=True, exist_ok=True)

### Requirement: daemon-state-path-resolution

The system SHALL provide `_daemon_state_path()` that returns the daemon state
JSON file path under `ZSIGA_HOME/data/daemon_state.json`.

#### Scenario: returns-daemon-state-json-path

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json`

### Requirement: read-daemon-state

The system SHALL provide `_read_daemon_state()` that reads and parses
`daemon_state.json`, returning an empty dict on any failure (file missing,
invalid JSON, OS error).

#### Scenario: returns-empty-dict-when-file-missing

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `ZSIGA_HOME` points to a directory with no `data/daemon_state.json`
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty dict `{}`

#### Scenario: returns-parsed-dict-when-valid-json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists with valid JSON `{"pid": 42, "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** the result equals `{"pid": 42, "cycle": 5}`

#### Scenario: returns-empty-dict-when-invalid-json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists but contains `not valid json`
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty dict `{}`

### Requirement: compute-uptime-seconds

The system SHALL provide `_compute_uptime_seconds(started_at)` that computes
elapsed seconds since the given ISO timestamp, rounded to 1 decimal place.
It MUST return `None` when input is falsy or unparseable.

#### Scenario: returns-none-for-none-input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: returns-none-for-empty-string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: returns-none-for-invalid-iso

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

#### Scenario: returns-positive-float-for-valid-recent-timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is the ISO string of 10 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a float >= 9.0 and <= 11.0
- **And** the result is rounded to 1 decimal place
