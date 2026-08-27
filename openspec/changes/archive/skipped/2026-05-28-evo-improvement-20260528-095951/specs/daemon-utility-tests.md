# daemon-utility-tests

## ADDED Requirements

### Requirement: Lock and state path resolution
`_lock_path()` and `_daemon_state_path()` SHALL resolve paths using the
`ZSIGA_HOME` environment variable when set, falling back to the repository root
(parent of the `zsiga` package directory) when unset. `_lock_path()` MUST create
the intermediate `data/` directory if it does not exist.

#### Scenario: lock path uses ZSIGA_HOME env var
- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-test-home`
- **When** `_lock_path()` is called
- **Then** the returned path equals `Path("/tmp/zsiga-test-home/data/lock.pid")`

#### Scenario: lock path falls back to repo root
- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is not set
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` and its parent directory exists

#### Scenario: daemon state path uses ZSIGA_HOME env var
- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-test-home`
- **When** `_daemon_state_path()` is called
- **Then** the returned path equals `Path("/tmp/zsiga-test-home/data/daemon_state.json")`

#### Scenario: daemon state path falls back to repo root
- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is not set
- **When** `_daemon_state_path()` is called
- **Then** the returned path ends with `data/daemon_state.json`

### Requirement: Read daemon state with safe defaults
`_read_daemon_state()` SHALL return an empty dict when the state file does not
exist, when it contains invalid JSON, or when an OS error occurs during read.
It MUST return the parsed dict when the file contains valid JSON.

#### Scenario: missing state file returns empty dict
- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: valid JSON state file returns parsed dict
- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the result equals `{"pid": 123, "state": "running"}`

#### Scenario: corrupted JSON returns empty dict
- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `not-valid-json{`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

### Requirement: Uptime computation
`_compute_uptime_seconds()` SHALL return `None` when `started_at` is falsy or
unparseable. When `started_at` is a valid ISO datetime string, it MUST return
the elapsed seconds rounded to 1 decimal place.

#### Scenario: None started_at returns None
- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: empty string started_at returns None
- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: invalid datetime returns None
- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-datetime"`
- **When** `_compute_uptime_seconds("not-a-datetime")` is called
- **Then** the result is `None`

#### Scenario: valid recent ISO datetime returns positive float
- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO datetime string 10 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a float >= 9.0 and has exactly 1 decimal place
