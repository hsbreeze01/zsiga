# daemon-unit-coverage

## ADDED Requirements

### Requirement: Path Helper Functions

`_lock_path()` and `_daemon_state_path()` SHALL resolve to paths under the
directory indicated by the `ZSIGA_HOME` environment variable, or fall back to
the repository root when that variable is unset. Both functions SHALL return a
`Path` object.

#### Scenario: Lock path uses ZSIGA_HOME

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` relative to that directory

#### Scenario: Lock path falls back to repo root

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is unset
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` and its parent directory exists (or is created)

#### Scenario: Daemon state path uses ZSIGA_HOME

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned path ends with `data/daemon_state.json` relative to that directory

#### Scenario: Daemon state path falls back to repo root

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is unset
- **When** `_daemon_state_path()` is called
- **Then** the returned path ends with `data/daemon_state.json`

---

### Requirement: Read Daemon State

`_read_daemon_state()` SHALL read and parse the daemon state JSON file if it
exists and contains valid JSON. It SHALL return an empty dict when the file is
missing, contains invalid JSON, or cannot be read.

#### Scenario: Returns parsed dict for valid JSON file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists and contains `{"pid": 1234, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 1234, "state": "running"}`

#### Scenario: Returns empty dict for missing file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: Returns empty dict for invalid JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists but contains `not-json`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

---

### Requirement: Lock Acquisition and Release

`acquire_lock()` SHALL obtain an exclusive non-blocking file lock on the PID
lock file. On success it SHALL return `(fd, True)` and write the current PID.
On failure (another process holds the lock) it SHALL return `(None, False)`.

`release_lock(fd)` SHALL close the file descriptor and remove the lock file,
silently tolerating `FileNotFoundError`.

#### Scenario: Acquire lock succeeds when no other holder

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** it returns a tuple where the second element is `True`

#### Scenario: Acquire lock writes PID to file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** lock is acquired successfully
- **When** the lock file content is read
- **Then** it contains the string representation of `os.getpid()`

#### Scenario: Release lock removes lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock was previously acquired
- **When** `release_lock(fd)` is called with that fd
- **Then** the lock file no longer exists

#### Scenario: Release lock tolerates missing file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file was already deleted
- **When** `release_lock(fd)` is called
- **Then** no exception is raised

---

### Requirement: Scan Proposal Queue

`_scan_proposal_queue(changes_dir)` SHALL walk the given changes directory and
return a list of dicts, one per subdirectory that contains a `proposal.md`.
Each dict SHALL include keys `name`, `project`, `summary`, `phase`,
`lifecycle`, `paused`, `paused_reason`, and `consecutive_fails`. It SHALL
return an empty list when the directory does not exist or contains no valid
proposal subdirectories.

#### Scenario: Returns empty list for non-existent directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a non-existent path
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: Returns entries for valid proposal directories

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory with a subdirectory `my-change` containing `proposal.md` with first heading `# Fix Bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list contains one entry with `name == "my-change"` and `summary == "Fix Bug"`

#### Scenario: Skips directories without proposal.md

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory with a subdirectory `empty-dir` containing no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list does not contain an entry with `name == "empty-dir"`

#### Scenario: Phase detection from output files

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `clarify.md` and a `specs/` directory with at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"IMPLEMENT"`

#### Scenario: Paused state from .paused file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that contains a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused == True` and `lifecycle == "paused"`

---

### Requirement: Compute Uptime Seconds

`_compute_uptime_seconds(started_at)` SHALL return the elapsed seconds (rounded
to 1 decimal) since the given ISO timestamp. It SHALL return `None` for `None`,
empty string, or unparseable input.

#### Scenario: Returns elapsed seconds for valid ISO timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp from the recent past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the returned value is a non-negative float rounded to 1 decimal

#### Scenario: Returns None for None input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** it returns `None`

#### Scenario: Returns None for empty string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** it returns `None`

#### Scenario: Returns None for invalid format

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** it returns `None`

---

### Requirement: Build Status and Metrics JSON

`_build_status_json()` SHALL return a JSON string containing a `daemon` object
(with keys `pid`, `state`, `cycle`, `current_change`, `current_phase`,
`current_project`, `heartbeat`, `uptime_seconds`) and a `queue` list.

`_build_metrics_json()` SHALL return a JSON string. When the metrics backend
fails, it SHALL return `{"error": "<message>"}`.

#### Scenario: Status JSON has daemon and queue keys

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns a dict with `state="running"` and `_scan_proposal_queue` returns an empty list
- **When** `_build_status_json()` is called
- **Then** the result is valid JSON containing keys `daemon` and `queue`

#### Scenario: Status JSON daemon object has required fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"state": "running", "started_at": "<recent ISO>"}`
- **When** the JSON is parsed
- **Then** the `daemon` object contains keys `pid`, `state`, `cycle`, `heartbeat`, `uptime_seconds`

#### Scenario: Metrics JSON returns error on backend failure

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** the metrics backend import raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the result is valid JSON containing an `error` key

#### Scenario: Metrics JSON returns summary on success

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` returns `{"summary": {"total": 5}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the parsed JSON contains a `summary` key with `total == 5`

