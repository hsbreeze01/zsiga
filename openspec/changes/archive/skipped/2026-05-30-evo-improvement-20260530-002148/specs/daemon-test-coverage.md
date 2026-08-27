# daemon-test-coverage

## ADDED Requirements

### Requirement: Path Helper Functions

The test file `tests/test_daemon.py` SHALL contain test cases that verify the behavior of `_lock_path()` and `_daemon_state_path()`.

`_lock_path()` MUST return a `Path` ending in `data/lock.pid` under the directory specified by the `ZSIGA_HOME` environment variable, defaulting to the repository root. The parent directory SHALL be created if it does not exist.

`_daemon_state_path()` MUST return a `Path` ending in `data/daemon_state.json` under the directory specified by the `ZSIGA_HOME` environment variable, defaulting to the repository root.

#### Scenario: _lock_path returns Path ending in data/lock.pid using ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid`
- **And** the parent directory exists

#### Scenario: _lock_path falls back to repo root when ZSIGA_HOME is unset

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is not set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid`
- **And** the parent directory of the returned path exists

#### Scenario: _daemon_state_path returns Path ending in data/daemon_state.json

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the `ZSIGA_HOME` environment variable is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json`

---

### Requirement: Read Daemon State

The test file SHALL verify that `_read_daemon_state()` returns the parsed contents of the daemon state JSON file when it exists and is valid, and returns an empty dict when the file is missing, contains invalid JSON, or cannot be read.

#### Scenario: _read_daemon_state returns empty dict when state file does not exist

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty dict `{}`

#### Scenario: _read_daemon_state returns parsed dict from valid JSON file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists and contains valid JSON `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the result equals `{"pid": 123, "state": "running"}`

#### Scenario: _read_daemon_state returns empty dict for malformed JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists but contains invalid JSON `{broken`
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty dict `{}`

---

### Requirement: Compute Uptime Seconds

The test file SHALL verify that `_compute_uptime_seconds()` returns the elapsed time in seconds (rounded to 1 decimal) since the given ISO timestamp, returns `None` for missing input, and returns `None` for unparseable timestamps.

#### Scenario: _compute_uptime_seconds returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: _compute_uptime_seconds returns None for empty string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: _compute_uptime_seconds returns None for unparseable string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

#### Scenario: _compute_uptime_seconds returns positive float for valid ISO timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp 10 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a float greater than 0
- **And** the result is rounded to 1 decimal place

---

### Requirement: Lock Lifecycle Functions

The test file SHALL verify that `acquire_lock()` returns `(fd, True)` when no lock is held, and that `release_lock(fd)` closes the file descriptor and removes the lock file.

#### Scenario: acquire_lock returns fd and True when lock is available

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** the return value is a tuple of `(file_object, True)`

#### Scenario: acquire_lock raises when lock is already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive lock on the lock file
- **When** `acquire_lock()` is called
- **Then** an exception is raised (the function attempts to read the PID from a write-only file descriptor)

#### Scenario: release_lock removes lock file and closes fd

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a valid file descriptor acquired from `acquire_lock()`
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

---

### Requirement: Scan Proposal Queue

The test file SHALL verify that `_scan_proposal_queue()` correctly discovers proposals in a changes directory, extracts summary headings from `proposal.md`, detects phase progress from output files, and returns an empty list for non-existent or empty directories.

#### Scenario: _scan_proposal_queue returns empty list for non-existent directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is a path to a non-existent directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: _scan_proposal_queue returns empty list for directory with no proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains subdirectories but none have a `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: _scan_proposal_queue discovers proposal with summary from heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `my-change/` with `proposal.md` whose first `# ` line is "My Great Proposal"
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list contains one entry with `name` equal to `"my-change"` and `summary` equal to `"My Great Proposal"`

#### Scenario: _scan_proposal_queue detects CLARIFY phase when only proposal.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory with `proposal.md` but no `clarify.md` and no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry has `phase` equal to `"CLARIFY"`

#### Scenario: _scan_proposal_queue detects ENRICH phase when clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory with `proposal.md` and `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry has `phase` equal to `"ENRICH"`

#### Scenario: _scan_proposal_queue detects IMPLEMENT phase when specs directory has markdown

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory with `proposal.md` and a `specs/` subdirectory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry has `phase` equal to `"IMPLEMENT"`

#### Scenario: _scan_proposal_queue skips non-directory entries

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a regular file named `notes.txt` alongside valid proposal directories
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the file `notes.txt` does not appear in the result entries

---

### Requirement: Build Status JSON

The test file SHALL verify that `_build_status_json()` returns a valid JSON string containing a `daemon` object and a `queue` array.

#### Scenario: _build_status_json returns valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"pid": 42, "state": "running", "started_at": "2026-01-01T00:00:00"}` and `_scan_proposal_queue` returns an empty list
- **When** `_build_status_json()` is called
- **Then** the result is a valid JSON string
- **And** parsing the result yields a dict with keys `"daemon"` and `"queue"`
- **And** `daemon["state"]` equals `"running"`

---

### Requirement: Build Metrics JSON

The test file SHALL verify that `_build_metrics_json()` returns a valid JSON string. When the metrics module raises an exception, it MUST return a JSON object with an `"error"` key.

#### Scenario: _build_metrics_json returns error JSON when metrics module fails

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** importing `compute_stats` raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the result is a valid JSON string containing an `"error"` key

---

### Requirement: Build Pipeline Status

The test file SHALL verify that `_build_pipeline_status()` returns a dict with the expected top-level keys and correctly identifies the active proposal from the daemon state.

#### Scenario: _build_pipeline_status returns dict with required keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** a temporary directory with an empty `openspec/changes/` directory, a valid SQLite database path, and daemon state with no current change
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result dict contains keys `"active_proposal"`, `"current_phase"`, `"phase_progress"`, `"queue"`, and `"daemon"`

#### Scenario: _build_pipeline_status identifies active proposal from daemon state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state has `current_change` set to `"test-change"` and `openspec/changes/test-change/` contains `proposal.md`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["active_proposal"]` equals `"test-change"`

---

### Requirement: Build Proposal Detail

The test file SHALL verify that `_build_proposal_detail()` returns a dict with proposal files, phase state, and DB record when available, and returns an error key when the proposal directory does not exist.

#### Scenario: _build_proposal_detail returns error for missing proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `openspec/changes/nonexistent-proposal/` does not exist and there is no matching archive entry
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-proposal")` is called
- **Then** the result dict contains key `"error"` with a string mentioning the proposal name

#### Scenario: _build_proposal_detail reads files from change directory

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `openspec/changes/my-proposal/` exists with `proposal.md` containing "# My Proposal" and `clarify.md` containing "some text"
- **When** `_build_proposal_detail(db_path, base_path, "my-proposal")` is called
- **Then** `result["files"]` contains keys `"proposal.md"` and `"clarify.md"`

---

### Requirement: Build Evolution Status

The test file SHALL verify that `_build_evolution_status()` returns a dict with keys `"enabled"`, `"window"`, `"state"`, and `"paused"`.

#### Scenario: _build_evolution_status returns dict with expected top-level keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_evolution_status
- **Given** a temporary directory with a valid zsiga.yaml config and the evolution engine is available
- **When** `_build_evolution_status(base_path)` is called
- **Then** the result dict contains keys `"enabled"`, `"window"`, `"state"`, and `"paused"`

---

### Requirement: Health Check

The test file SHALL verify that `_health_check()` returns a healthy status dict for a valid database and an unhealthy status dict when the database is inaccessible.

#### Scenario: _health_check returns healthy for valid database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a valid SQLite database file with a `changes` table containing 5 rows
- **When** `_health_check(db_path)` is called
- **Then** `result["status"]` equals `"healthy"` and `result["db_records"]` equals 5

#### Scenario: _health_check returns unhealthy for invalid path

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a database path that does not exist
- **When** `_health_check(db_path)` is called
- **Then** `result["status"]` equals `"unhealthy"` and `result` contains key `"error"`
