# daemon-path-state — Path & State Utility Functions

## ADDED Requirements

### Requirement: Lock file path resolution

`_lock_path()` SHALL return a `Path` object ending in `data/lock.pid`. The `data` directory
MUST be created automatically if it does not exist. The base directory is derived from the
`ZSIGA_HOME` environment variable when set; otherwise it falls back to the repository root
(two levels above the daemon module).

#### Scenario: lock path with ZSIGA_HOME env var

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the result is a `Path` equal to `<ZSIGA_HOME>/data/lock.pid`
- **And** the `data` subdirectory exists on disk

#### Scenario: lock path creates data directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable points to a directory without a `data` subdirectory
- **When** `_lock_path()` is called
- **Then** the directory `<ZSIGA_HOME>/data` is created and exists

---

### Requirement: Daemon state file path resolution

`_daemon_state_path()` SHALL return a `Path` object ending in `data/daemon_state.json`.
Unlike `_lock_path`, it SHALL NOT create the `data` directory automatically.

#### Scenario: state path with ZSIGA_HOME env var

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the `ZSIGA_HOME` environment variable is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the result is a `Path` equal to `<ZSIGA_HOME>/data/daemon_state.json`

---

### Requirement: Reading daemon state JSON

`_read_daemon_state()` SHALL read `daemon_state.json` and return its contents as a `dict`.
If the file does not exist or contains invalid JSON, it SHALL return an empty `dict` without
raising an exception.

#### Scenario: read state when file does not exist

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist on disk
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty `dict`

#### Scenario: read state with valid JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists and contains valid JSON `{"pid": 42, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{"pid": 42, "state": "running"}`

#### Scenario: read state with invalid JSON degrades gracefully

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists and contains invalid JSON text `"not json"`
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty `dict`

---

### Requirement: Writing daemon state JSON

`_write_daemon_state()` SHALL write a JSON file with the provided fields plus derived fields
(`pid`, `last_heartbeat`). Fields not explicitly provided SHALL be inherited from the existing
state file. The file and parent directories SHALL be created if they do not exist.

#### Scenario: write state creates file with required fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_write_daemon_state
- **Given** the daemon state file does not exist
- **When** `_write_daemon_state(started_at="2026-01-01T00:00:00", cycle=1, state="running")` is called
- **Then** the daemon state file exists on disk
- **And** the JSON content contains `"started_at": "2026-01-01T00:00:00"`, `"cycle": 1`, `"state": "running"`, and a numeric `"pid"`

#### Scenario: write state preserves existing fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_write_daemon_state
- **Given** the daemon state file exists with `{"total_cycles": 5}`
- **When** `_write_daemon_state(started_at="2026-01-01T00:00:00", cycle=2)` is called without `total_cycles`
- **Then** the resulting JSON contains `"total_cycles": 5` inherited from the existing file

---

### Requirement: PID lock acquisition and release

`acquire_lock()` SHALL acquire an exclusive non-blocking file lock using `fcntl`. On success
it returns `(fd, True)` where `fd` is an open file descriptor. On failure (another process holds
the lock), it returns `(None, False)` without raising. `release_lock(fd)` SHALL close the fd
and remove the lock file.

#### Scenario: acquire lock succeeds on fresh lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** the return value is `(fd, True)` where `fd` is not `None`
- **And** the lock file contains the current process PID as text

#### Scenario: release lock removes lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock has been acquired via `acquire_lock()` returning `(fd, True)`
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

