# daemon-unit-tests

## ADDED Requirements

### Requirement: Path utility functions SHALL resolve via ZSIGA_HOME

`_lock_path()` and `_daemon_state_path()` SHALL resolve paths relative to the
`ZSIGA_HOME` environment variable when set, falling back to the repo root when
the variable is absent. `_lock_path()` SHALL also create the `data/` directory
if it does not exist.

#### Scenario: _lock_path returns data/lock.pid under ZSIGA_HOME

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned path SHALL equal `<ZSIGA_HOME>/data/lock.pid`

#### Scenario: _lock_path creates data directory if missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory where `data/` does not exist
- **When** `_lock_path()` is called
- **Then** the `data/` directory SHALL exist after the call and the returned path SHALL end with `data/lock.pid`

#### Scenario: _daemon_state_path returns data/daemon_state.json under ZSIGA_HOME

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned path SHALL equal `<ZSIGA_HOME>/data/daemon_state.json`

---

### Requirement: _read_daemon_state SHALL return parsed JSON or empty dict

`_read_daemon_state()` SHALL read `daemon_state.json` and return its parsed
contents as a dict. When the file is missing or contains invalid JSON, it SHALL
return an empty dict.

#### Scenario: _read_daemon_state returns dict from valid JSON file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a `daemon_state.json` file exists under the mocked ZSIGA_HOME containing `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it SHALL return `{"pid": 123, "state": "running"}`

#### Scenario: _read_daemon_state returns empty dict when file is missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no `daemon_state.json` file exists under the mocked ZSIGA_HOME
- **When** `_read_daemon_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: _read_daemon_state returns empty dict for malformed JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a `daemon_state.json` file exists under the mocked ZSIGA_HOME containing `not-valid-json`
- **When** `_read_daemon_state()` is called
- **Then** it SHALL return `{}`

---

### Requirement: acquire_lock and release_lock SHALL manage PID file lock

`acquire_lock()` SHALL use `fcntl.flock` with `LOCK_EX | LOCK_NB` to obtain an
exclusive non-blocking lock. On success it SHALL return `(fd, True)` with the
current PID written to the lock file. On failure it SHALL return `(None, False)`.
`release_lock(fd)` SHALL close the file descriptor and remove the lock file,
silently ignoring `FileNotFoundError`.

#### Scenario: acquire_lock succeeds when no other lock is held

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory and no lock file exists
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be a tuple where the second element is `True` and the lock file SHALL contain the current process PID

#### Scenario: acquire_lock fails when flock raises OSError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `fcntl.flock` is mocked to raise `OSError`
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be `(None, False)`

#### Scenario: release_lock closes fd and removes lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists at the expected path and a writable file descriptor is open on it
- **When** `release_lock(fd)` is called
- **Then** the lock file SHALL no longer exist on disk

#### Scenario: release_lock ignores FileNotFoundError gracefully

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has already been deleted before the call
- **When** `release_lock(fd)` is called
- **Then** no exception SHALL be raised

---

### Requirement: _compute_uptime_seconds SHALL compute elapsed time

`_compute_uptime_seconds(started_at)` SHALL parse an ISO-format datetime string
and return the elapsed seconds since that time, rounded to 1 decimal place. It
SHALL return `None` for empty, `None`, or unparseable inputs.

#### Scenario: _compute_uptime_seconds returns elapsed seconds for valid ISO string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `datetime.now` is mocked to return a fixed timestamp and `started_at` is a valid ISO string 90 seconds before that timestamp
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** it SHALL return `90.0`

#### Scenario: _compute_uptime_seconds returns None for None input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** it SHALL return `None`

#### Scenario: _compute_uptime_seconds returns None for empty string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** it SHALL return `None`

#### Scenario: _compute_uptime_seconds returns None for unparseable string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** it SHALL return `None`

---

### Requirement: _build_status_json SHALL produce valid JSON with daemon and queue keys

`_build_status_json()` SHALL return a JSON string containing a top-level object
with a `"daemon"` key. The `"daemon"` object SHALL include `"state"`,
`"uptime_seconds"`, and `"pid"` fields sourced from `_read_daemon_state`.

#### Scenario: _build_status_json returns valid JSON with daemon key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` is mocked to return `{"pid": 42, "state": "running", "started_at": "2025-01-01T00:00:00", "cycle": 5}` and `_scan_proposal_queue` is mocked to return an empty list and `_compute_uptime_seconds` is mocked to return `100.0`
- **When** `_build_status_json()` is called
- **Then** the result SHALL be a valid JSON string containing `"daemon"` key with `"state": "running"` and `"uptime_seconds": 100.0`

---

### Requirement: _build_metrics_json SHALL produce valid JSON with summary key

`_build_metrics_json()` SHALL return a JSON string with a `"summary"` key when
the metrics module is available, or a JSON string with an `"error"` key when an
exception occurs.

#### Scenario: _build_metrics_json returns valid JSON with summary on success

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `zsiga.metrics.dashboard.compute_stats` is mocked to return `{"summary": {"total": 10}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the result SHALL be a valid JSON string containing `"summary"` key

#### Scenario: _build_metrics_json returns error JSON on exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `zsiga.metrics.dashboard.compute_stats` is mocked to raise `RuntimeError("db locked")`
- **When** `_build_metrics_json()` is called
- **Then** the result SHALL be a valid JSON string containing `"error": "db locked"`

