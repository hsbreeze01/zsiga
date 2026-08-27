# daemon-unit-tests

## Context
`zsiga/daemon.py` (1110 lines) has partial test coverage via 3 existing test files
(`test_daemon_state.py`, `test_daemon_scheduling.py`, `test_daemon_cycle_resilience.py`).
Multiple functions — including high-complexity ones — remain uncovered. This spec
defines the behavioural contract that the new `tests/test_daemon.py` SHALL validate.

---

## ADDED Requirements

### Requirement: Pure path helpers return correct paths

`_lock_path()` and `_daemon_state_path()` SHALL resolve to the expected file paths
under the `ZSIGA_HOME` environment variable (or repo root when unset).

#### Scenario: lock_path with ZSIGA_HOME set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/lock.pid` and the `data/` directory has been created

#### Scenario: lock_path with ZSIGA_HOME unset

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and its parent is `data/`

#### Scenario: daemon_state_path with ZSIGA_HOME set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/daemon_state.json`

---

### Requirement: _read_daemon_state returns dict from JSON file or empty dict

`_read_daemon_state()` SHALL read the daemon state JSON file and return its contents
as a dict. When the file does not exist or contains invalid JSON, it SHALL return an
empty dict.

#### Scenario: read existing valid state file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists and contains `{"pid": 123, "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 123, "cycle": 5}`

#### Scenario: read when state file missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: read when state file contains invalid JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file exists and contains `not valid json{`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

---

### Requirement: _compute_uptime_seconds computes elapsed time correctly

`_compute_uptime_seconds(started_at)` SHALL return the number of seconds (rounded to
1 decimal) between the ISO-format `started_at` timestamp and the current time. It SHALL
return `None` for missing or unparseable input.

#### Scenario: valid ISO timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an ISO-format string 60 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the returned value is approximately 60.0 (±5 seconds)

#### Scenario: None input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the returned value is `None`

#### Scenario: empty string input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the returned value is `None`

#### Scenario: invalid timestamp string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the returned value is `None`

---

### Requirement: _build_status_json produces valid JSON with daemon and queue keys

`_build_status_json()` SHALL return a JSON string containing top-level `"daemon"` and
`"queue"` keys. The daemon object SHALL include at minimum `"state"`, `"pid"`,
`"cycle"`, `"current_change"`, `"current_phase"`, `"current_project"`, `"heartbeat"`,
and `"uptime_seconds"` fields.

#### Scenario: status JSON structure with empty daemon state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state file is empty and no changes directory exists
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON, contains `"daemon"` dict with key `"state"` equal to `"unknown"`, and `"queue"` list

#### Scenario: status JSON includes uptime_seconds

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state file contains `{"started_at": "<recent ISO timestamp>"}`
- **When** `_build_status_json()` is called
- **Then** the parsed JSON's `daemon.uptime_seconds` is a non-negative number

---

### Requirement: _build_metrics_json returns valid JSON

`_build_metrics_json()` SHALL return a JSON string. When the metrics subsystem is
unavailable it SHALL return `{"error": "<message>"}`.

#### Scenario: metrics json is parseable JSON

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** the metrics subsystem may or may not be available
- **When** `_build_metrics_json()` is called
- **Then** the result is a valid JSON string (parseable by `json.loads`)

---

### Requirement: acquire_lock obtains exclusive PID lock

`acquire_lock()` SHALL create a lock file, write the current PID, and return
`(fd, True)` on success. If another process holds the lock, it SHALL return
`(None, False)`.

#### Scenario: successful lock acquisition

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** it returns a tuple whose second element is `True` and the lock file contains the current PID as text

#### Scenario: lock contention returns failure

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive lock on the lock file
- **When** `acquire_lock()` is called
- **Then** it returns `(None, False)`

---

### Requirement: release_lock closes fd and removes lock file

`release_lock(fd)` SHALL close the file descriptor and remove the lock file.

#### Scenario: release removes lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and an open file descriptor `fd` references it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: release handles already-deleted lock file gracefully

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file has been manually deleted and an open file descriptor `fd` references it
- **When** `release_lock(fd)` is called
- **Then** no exception is raised

---

### Requirement: _scan_proposal_queue classifies proposals by phase and lifecycle

`_scan_proposal_queue(changes_dir)` SHALL walk a changes directory, identify proposals,
and classify each by phase (CLARIFY/ENRICH/IMPLEMENT) and lifecycle status. It SHALL
return a list of dicts each containing `"name"`, `"project"`, `"summary"`, `"phase"`,
`"lifecycle"`, `"paused"`, and `"paused_reason"` keys.

#### Scenario: empty changes directory returns empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** the changes directory is empty
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: non-directory changes_dir returns empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a non-existent path
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: proposal with only proposal.md has phase CLARIFY

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes subdirectory `my-change/` contains only `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `my-change` has `"phase"` equal to `"CLARIFY"`

#### Scenario: proposal with clarify.md has phase ENRICH

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes subdirectory `my-change/` contains `proposal.md` and `clarify.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `my-change` has `"phase"` equal to `"ENRICH"`

#### Scenario: proposal with specs/ directory has phase IMPLEMENT

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes subdirectory `my-change/` contains `proposal.md`, `clarify.md`, and `specs/` with at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `my-change` has `"phase"` equal to `"IMPLEMENT"`

#### Scenario: summary extracted from first heading in proposal.md

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal.md whose first `# ` line reads `# Add health check`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `"summary"` equals `"Add health check"`

#### Scenario: manual .paused file sets paused=true

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes subdirectory contains `proposal.md` and `.paused`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `"paused"` equal to `True` and `"paused_reason"` equal to `"manual"`

---

### Requirement: _build_pipeline_status returns structured dict

`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys
`"active_proposal"`, `"current_phase"`, `"phase_progress"`, `"queue"`, and `"daemon"`.

#### Scenario: no active proposal and empty directories

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** the daemon state is empty, the changes directory is empty, and db_path points to a non-existent file
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result dict contains `"active_proposal"` equal to `None`, `"queue"` as an empty list, and `"phase_progress"` as an empty list

#### Scenario: daemon key contains state and cycle

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** the daemon state file contains `{"state": "running", "cycle": 7, "started_at": "<recent ISO>"}`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["daemon"]["state"]` equals `"running"` and `result["daemon"]["cycle"]` equals 7

---

### Requirement: _build_proposal_detail returns files and phase state

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict with
keys `"proposal_name"`, `"files"`, `"phases"`, and `"phase_state"`. When the proposal
directory does not exist, it SHALL include an `"error"` key.

#### Scenario: non-existent proposal returns error

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no directory matching `proposal_name` exists under changes or archive
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-proposal")` is called
- **Then** the result contains key `"error"` with a string value mentioning the proposal name

#### Scenario: existing proposal with proposal.md includes file content

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory containing `proposal.md` with content `# My Proposal`
- **When** `_build_proposal_detail(db_path, base_path, "<proposal_name>")` is called
- **Then** `result["files"]["proposal.md"]` contains `"My Proposal"`

#### Scenario: phase_state file is read into phase_state key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory containing `.phase_state` with `{"current_phase": "IMPLEMENT"}`
- **When** `_build_proposal_detail(db_path, base_path, "<proposal_name>")` is called
- **Then** `result["phase_state"]["current_phase"]` equals `"IMPLEMENT"`

---

### Requirement: _health_check reports database health

`_health_check(db_path)` SHALL return `{"status": "healthy", "db_records": <int>}` on
success or `{"status": "unhealthy", "error": "<message>"}` on failure.

#### Scenario: healthy database

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "healthy", "db_records": 3}`

#### Scenario: non-existent database file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a non-existent file
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "unhealthy", "error": "<some message>"}`

---

### Requirement: _build_proposal_stats_json returns aggregate statistics

`_build_proposal_stats_json(db_path)` SHALL return a dict with `"total"`, `"by_outcome"`,
`"avg_duration_seconds"`, and `"recent"` keys, or `{"error": "<message>"}` on failure.

#### Scenario: non-existent database returns error dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains key `"error"` with a string value

#### Scenario: database without changes table returns error dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database at `db_path` with no `changes` table
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains key `"error"` with string value mentioning "changes table"

---

### Requirement: Test file structure and isolation

`tests/test_daemon.py` SHALL exist, contain ≥ 15 test functions, and every test
SHALL use `tmp_path` / `monkeypatch` for filesystem isolation so that tests pass
without a running daemon or specific runtime environment.

#### Scenario: test file exists and has minimum test count

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the change has been implemented
- **When** the file `tests/test_daemon.py` is inspected
- **Then** it exists and contains at least 15 `def test_` function definitions

#### Scenario: all tests pass

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the change has been implemented
- **When** `python -m pytest tests/test_daemon.py` is executed
- **Then** the exit code is 0

