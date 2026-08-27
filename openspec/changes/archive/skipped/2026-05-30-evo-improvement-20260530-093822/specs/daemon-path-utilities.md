# daemon-path-utilities

## ADDED Requirements

### Requirement: Path computation utilities SHALL resolve via ZSIGA_HOME

`_lock_path()` and `_daemon_state_path()` SHALL use the `ZSIGA_HOME`
environment variable (falling back to the repo root) to derive their
return values.

#### Scenario: lock path resolved under ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-test-home`
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and its parent starts with `/tmp/zsiga-test-home`

#### Scenario: daemon state path resolved under ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-test-home`
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` equals `Path("/tmp/zsiga-test-home/data/daemon_state.json")`

#### Scenario: lock path creates data directory

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** `ZSIGA_HOME` is set to a temporary directory that does **not** contain a `data/` subdirectory
- **When** `_lock_path()` is called
- **Then** the `data/` directory SHALL exist on disk after the call

---

### Requirement: _read_daemon_state SHALL return dict from JSON or empty dict

`_read_daemon_state()` SHALL read `daemon_state.json` if it exists and is
valid JSON, otherwise return an empty dict.

#### Scenario: read existing valid state file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `_daemon_state_path()` returns a path containing valid JSON `{"pid": 123, "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** it SHALL return `{"pid": 123, "cycle": 5}`

#### Scenario: read missing state file returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `_daemon_state_path()` returns a path to a non-existent file
- **When** `_read_daemon_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: read corrupt JSON returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `_daemon_state_path()` returns a path containing `{invalid json!!!`
- **When** `_read_daemon_state()` is called
- **Then** it SHALL return `{}`

---

### Requirement: _compute_uptime_seconds SHALL return elapsed time or None

`_compute_uptime_seconds()` SHALL compute the elapsed seconds since the
given ISO timestamp, rounded to 1 decimal. Returns `None` on missing or
invalid input.

#### Scenario: valid ISO timestamp returns positive float

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** a valid ISO timestamp string representing 10 seconds ago (mocked `datetime.now`)
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** it SHALL return a `float` that is approximately `10.0`

#### Scenario: None input returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** it SHALL return `None`

#### Scenario: empty string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** it SHALL return `None`

#### Scenario: invalid string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** it SHALL return `None`

---

### Requirement: DaemonState SHALL default to not paused and not shutdown

#### Scenario: default DaemonState values

- **testable**: true
- **target**: zsiga/daemon.py::DaemonState
- **Given** a new `DaemonState` instance
- **When** its `paused` and `shutdown` attributes are read
- **Then** both SHALL be `False`
