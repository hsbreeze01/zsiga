# daemon-utility-functions

## ADDED Requirements

### Requirement: Path helpers return consistent paths based on ZSIGA_HOME

`_lock_path()` and `_daemon_state_path()` SHALL resolve their return values
relative to `ZSIGA_HOME` env-var (or the repo root fallback) and MUST always
return a `Path` object whose parent directory is `data/` inside that home.

#### Scenario: _lock_path returns data/lock.pid under ZSIGA_HOME

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` env-var is set to `/tmp/zsiga-test-home`
- **When** `_lock_path()` is called
- **Then** the result is a `Path` ending with `data/lock.pid` under that home

#### Scenario: _daemon_state_path returns data/daemon_state.json under ZSIGA_HOME

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the `ZSIGA_HOME` env-var is set to `/tmp/zsiga-test-home`
- **When** `_daemon_state_path()` is called
- **Then** the result is a `Path` ending with `data/daemon_state.json` under that home

#### Scenario: _lock_path creates parent directory if absent

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** `ZSIGA_HOME` points to a temporary directory that does not contain `data/`
- **When** `_lock_path()` is called
- **Then** the `data/` directory is created and exists on disk

### Requirement: _read_daemon_state reads or returns empty dict

`_read_daemon_state()` SHALL parse the daemon state JSON file. If the file is
missing, empty, or malformed, it MUST return an empty `dict`.

#### Scenario: _read_daemon_state returns empty dict when file missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no `daemon_state.json` file exists at the state path
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: _read_daemon_state returns empty dict on malformed JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a `daemon_state.json` file containing invalid JSON (`NOT JSON`)
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: _read_daemon_state returns parsed dict on valid JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a `daemon_state.json` file containing `{"state": "running", "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{"state": "running", "cycle": 5}`

### Requirement: _compute_uptime_seconds returns elapsed time or None

`_compute_uptime_seconds(started_at)` SHALL compute the number of seconds
between the given ISO timestamp and now, rounded to 1 decimal. It MUST return
`None` for `None`, empty string, or unparseable input.

#### Scenario: _compute_uptime_seconds returns None for None input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: _compute_uptime_seconds returns None for empty string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: _compute_uptime_seconds returns positive float for valid timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO datetime string in the past (e.g. 60 seconds ago)
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` ≥ 0, rounded to 1 decimal place

#### Scenario: _compute_uptime_seconds returns None for invalid timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

### Requirement: DaemonState dataclass provides signal-handler flags

`DaemonState` SHALL be a class with two boolean class-level attributes:
`paused` (default `False`) and `shutdown` (default `False`).

#### Scenario: DaemonState defaults to not paused and not shutdown

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::DaemonState
- **Given** a freshly constructed `DaemonState` instance
- **When** the `paused` and `shutdown` attributes are read
- **Then** both are `False`

### Requirement: acquire_lock and release_lock manage PID file

`acquire_lock()` SHALL attempt an exclusive non-blocking flock on the lock
file. On success it returns `(fd, True)` and writes the current PID. On failure
(another process holds the lock) it returns `(None, False)`. `release_lock(fd)`
SHALL close the fd and remove the lock file.

#### Scenario: acquire_lock succeeds on fresh lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no existing lock file and the state path is writable
- **When** `acquire_lock()` is called
- **Then** the result is `(fd, True)` and the lock file contains the current PID string

#### Scenario: release_lock removes lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and an open fd to it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: acquire_lock fails when another process holds the lock

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another process holds the flock on the lock file
- **When** `acquire_lock()` is called
- **Then** the result is `(None, False)`

