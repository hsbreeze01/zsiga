# phase-daemon-utility-tests.md

## ADDED Requirements

### Requirement: daemon-path-utility-tests
The test suite SHALL verify that `_lock_path()`, `_daemon_state_path()`, `_read_daemon_state()`, `_compute_uptime_seconds()`, and `DaemonState` behave correctly for all input conditions including env-var override, default fallback, missing files, and corrupt JSON.

#### Scenario: lock-path-uses-zsiga-home-env

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned path SHALL equal `Path(ZSIGA_HOME) / "data" / "lock.pid"`

#### Scenario: lock-path-default-without-env

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is not set
- **When** `_lock_path()` is called
- **Then** the returned path SHALL end with `data/lock.pid` and the parent directory `data` SHALL exist

#### Scenario: daemon-state-path-uses-zsiga-home-env

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned path SHALL equal `Path(ZSIGA_HOME) / "data" / "daemon_state.json"`

#### Scenario: read-daemon-state-existing-file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a valid `daemon_state.json` file exists containing `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called (with path monkeypatched to the test file)
- **Then** the result SHALL be `{"pid": 123, "state": "running"}`

#### Scenario: read-daemon-state-missing-file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no `daemon_state.json` file exists at the target path
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`

#### Scenario: read-daemon-state-corrupt-json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a `daemon_state.json` file exists containing invalid JSON text `"not valid {json"`
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`

#### Scenario: compute-uptime-valid-timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an ISO timestamp 100 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result SHALL be approximately 100.0 (within ±2 seconds tolerance) and SHALL be rounded to 1 decimal place

#### Scenario: compute-uptime-none-input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result SHALL be `None`

#### Scenario: compute-uptime-empty-string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result SHALL be `None`

#### Scenario: daemon-state-defaults

- **testable**: true
- **target**: zsiga/daemon.py::DaemonState
- **Given** a new `DaemonState` instance is created
- **When** the `paused` and `shutdown` attributes are inspected
- **Then** `paused` SHALL be `False` and `shutdown` SHALL be `False`
