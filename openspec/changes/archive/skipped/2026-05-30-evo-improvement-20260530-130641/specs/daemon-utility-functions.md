# daemon-utility-functions

Delta spec for testing low-level utility functions in `zsiga/daemon.py`
that have no direct test coverage yet.

## ADDED Requirements

### Requirement: Lock path resolution

The system SHALL resolve the PID lock file path by reading the
`ZSIGA_HOME` environment variable and appending `data/lock.pid`.
When `ZSIGA_HOME` is unset, the system SHALL fall back to the
parent directory of the package root.

#### Scenario: Lock path with ZSIGA_HOME set

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zh`
- **When** `_lock_path()` is called
- **Then** the returned path equals `Path("/tmp/zh/data/lock.pid")`
- **And** the `data/` directory has been created

#### Scenario: Lock path with ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is unset
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid`
- **And** its parent's parent equals the repo root

---

### Requirement: Daemon state path resolution

The system SHALL resolve the daemon state file path by reading the
`ZSIGA_HOME` environment variable and appending
`data/daemon_state.json`. When `ZSIGA_HOME` is unset the same
fallback as `_lock_path` SHALL apply.

#### Scenario: State path with ZSIGA_HOME set

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zh2`
- **When** `_daemon_state_path()` is called
- **Then** the returned path equals `Path("/tmp/zh2/data/daemon_state.json")`

#### Scenario: State path without ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is unset
- **When** `_daemon_state_path()` is called
- **Then** the returned path ends with `data/daemon_state.json`

---

### Requirement: Read daemon state

The system SHALL read and parse `daemon_state.json`. When the file
does not exist or contains invalid JSON, the system SHALL return an
empty dict.

#### Scenario: File exists with valid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file containing `{"pid": 42, "cycle": 3}`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{"pid": 42, "cycle": 3}`

#### Scenario: File does not exist

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no daemon state file exists
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{}`

#### Scenario: File contains invalid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file containing `not-json`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{}`

---

### Requirement: Lock acquisition

`acquire_lock()` SHALL attempt an exclusive non-blocking file lock.
On success it SHALL return `(fd, True)` and write the current PID to
the lock file. On failure (another process holds the lock) it SHALL
return `(None, False)`.

#### Scenario: Successful lock acquisition

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** a writable lock file path with `fcntl.flock` mocked to succeed
- **When** `acquire_lock()` is called
- **Then** the return value is `(fd, True)` where `fd` is an open file descriptor
- **And** the lock file contains the current process PID

#### Scenario: Lock contention failure

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `fcntl.flock` raises `OSError`
- **When** `acquire_lock()` is called
- **Then** the return value is `(None, False)`

---

### Requirement: Lock release

`release_lock(fd)` SHALL close the file descriptor and remove the
lock file. It SHALL silently ignore `FileNotFoundError`.

#### Scenario: Successful release

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** an open file descriptor for an existing lock file
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists

#### Scenario: Release with already-deleted lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has been deleted externally
- **When** `release_lock(fd)` is called
- **Then** no exception is raised

---

### Requirement: Uptime computation

`_compute_uptime_seconds(started_at)` SHALL compute elapsed seconds
since the given ISO timestamp, rounded to 1 decimal. It SHALL return
`None` when the input is `None`, empty, or unparseable.

#### Scenario: Valid ISO timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp 60 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is approximately `60.0` (±2.0 seconds)

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

#### Scenario: Invalid timestamp returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`
