# daemon-unit-tests

## ADDED Requirements

### Requirement: lock_path_resolves_to_data_dir
`_lock_path()` SHALL return a `Path` ending with `data/lock.pid`. When `ZSIGA_HOME` is set, the path SHALL be relative to that environment variable; otherwise it SHALL be relative to the repository root (parent of the `zsiga` package directory). The `data` directory SHALL be created automatically if it does not exist.

#### Scenario: lock_path_with_zsiga_home_env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory path
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and the `data` subdirectory exists

#### Scenario: lock_path_default_without_env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` under the repo root

---

### Requirement: daemon_state_path_resolves_to_json
`_daemon_state_path()` SHALL return a `Path` ending with `data/daemon_state.json`. When `ZSIGA_HOME` is set, the path SHALL be relative to that environment variable; otherwise it SHALL be relative to the repository root.

#### Scenario: daemon_state_path_with_zsiga_home_env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory path
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json`

---

### Requirement: read_daemon_state_returns_existing_state
`_read_daemon_state()` SHALL read the daemon state JSON file and return it as a dict. If the file does not exist, it SHALL return an empty dict. If the file exists but contains invalid JSON, it SHALL also return an empty dict without raising an exception.

#### Scenario: read_state_from_existing_valid_file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state JSON file exists and contains `{"pid": 1234, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{"pid": 1234, "state": "running"}`

#### Scenario: read_state_missing_file_returns_empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state JSON file does not exist
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{}`

#### Scenario: read_state_corrupted_json_returns_empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state JSON file exists but contains `not valid json {{{`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{}` and no exception is raised

---

### Requirement: compute_uptime_seconds
`_compute_uptime_seconds(started_at)` SHALL return the elapsed time in seconds (rounded to 1 decimal) between the given ISO timestamp and `datetime.now()`. When `started_at` is `None` or an unparseable string, it SHALL return `None`.

#### Scenario: compute_uptime_valid_timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp 5 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` approximately equal to 5.0 (within ±2 seconds tolerance) and rounded to 1 decimal

#### Scenario: compute_uptime_none_returns_none

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: compute_uptime_empty_string_returns_none

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: compute_uptime_invalid_string_returns_none

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

---

### Requirement: build_status_json_structure
`_build_status_json()` SHALL return a valid JSON string containing a top-level object with keys `"daemon"` and `"queue"`. The `"daemon"` object SHALL contain keys `"pid"`, `"state"`, `"cycle"`, `"current_change"`, `"current_phase"`, `"current_project"`, `"heartbeat"`, and `"uptime_seconds"`. The `"queue"` value SHALL be a list.

#### Scenario: build_status_json_valid_structure

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"pid": 42, "state": "running", "cycle": 1, "started_at": "<recent ISO timestamp>"}` and `_scan_proposal_queue` returns an empty list (via monkeypatch)
- **When** `_build_status_json()` is called
- **Then** the result is valid JSON parseable with `json.loads`, and the parsed object has keys `"daemon"` and `"queue"`, where `"daemon"` has key `"pid"` equal to 42, and `"queue"` is a list

---

### Requirement: build_metrics_json_structure
`_build_metrics_json()` SHALL return a valid JSON string. When `compute_stats()` succeeds, the JSON SHALL contain `"summary"` and `"phases"` keys. When `compute_stats()` raises an exception, the JSON SHALL contain an `"error"` key with a non-empty string value.

#### Scenario: build_metrics_json_on_exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` raises `RuntimeError("db unavailable")` (via monkeypatch of `zsiga.metrics.dashboard.compute_stats`)
- **When** `_build_metrics_json()` is called
- **Then** the result is valid JSON, and `json.loads(result)` contains key `"error"` with value `"db unavailable"`

---

### Requirement: scan_proposal_queue_basic
`_scan_proposal_queue(changes_dir)` SHALL scan the given changes directory for subdirectories containing `proposal.md` files and return a list of dicts. When `changes_dir` is `None`, it SHALL resolve to `$ZSIGA_HOME/openspec/changes`. When the directory does not exist, it SHALL return an empty list. Each returned entry SHALL have keys `"name"`, `"project"`, `"summary"`, `"phase"`, `"lifecycle"`, `"paused"`, `"paused_reason"`, and `"consecutive_fails"`.

#### Scenario: scan_nonexistent_directory_returns_empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a non-existent directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list `[]`

#### Scenario: scan_directory_with_proposal_md

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `my-change` with a `proposal.md` whose first line starting with `# ` is `# Fix logging bug`
- **When** `_scan_proposal_queue(changes_dir)` is called (with `load_config` and `load_all_changes` monkeypatched to avoid external deps)
- **Then** the result list has length 1, the first entry has `"name"` equal to `"my-change"` and `"summary"` equal to `"Fix logging bug"`

#### Scenario: scan_skips_dirs_without_proposal_md

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `no-proposal` without a `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called (with deps monkeypatched)
- **Then** the result list is empty

#### Scenario: scan_skips_non_directory_entries

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a regular file named `not-a-dir.md`
- **When** `_scan_proposal_queue(changes_dir)` is called (with deps monkeypatched)
- **Then** the result list is empty

#### Scenario: scan_detects_phase_from_files

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `phased-change` with `proposal.md`, `clarify.md`, and a `specs/` directory containing `some-spec.md`
- **When** `_scan_proposal_queue(changes_dir)` is called (with deps monkeypatched)
- **Then** the first entry has `"phase"` equal to `"IMPLEMENT"`

---

### Requirement: acquire_lock_mutual_exclusion
`acquire_lock()` SHALL attempt to acquire an exclusive non-blocking file lock on the PID lock file. On success, it SHALL return `(fd, True)` where `fd` is an open file object. On failure (another process holds the lock), it SHALL return `(None, False)` and close the file descriptor.

#### Scenario: acquire_lock_success

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock (lock file does not exist)
- **When** `acquire_lock()` is called
- **Then** the result tuple has `result[1] is True` and `result[0]` is a non-None file object

#### Scenario: acquire_lock_contention_returns_false

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another `acquire_lock()` call has already acquired the lock in the same test process
- **When** a second `acquire_lock()` is called from a subprocess that also tries `fcntl.LOCK_EX | fcntl.LOCK_NB`
- **Then** the subprocess fails to acquire the lock (non-zero exit code or no "acquired" in stdout)

---

### Requirement: release_lock_cleans_up
`release_lock(fd)` SHALL close the file descriptor and remove the lock file. If the lock file has already been removed, it SHALL not raise an exception.

#### Scenario: release_lock_removes_file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock has been acquired and the lock file exists on disk
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: release_lock_idempotent_no_error

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock has been acquired and then released (lock file removed)
- **When** `release_lock(fd)` is called with a fresh fd to a new lock path where the file was already removed
- **Then** no exception is raised

---

### Requirement: build_proposal_stats_json_basic
`_build_proposal_stats_json(db_path)` SHALL query a SQLite database for aggregate proposal statistics. When the database file does not exist, it SHALL return `{"error": "Database file not found: ..."}`. When the database exists and has a valid `changes` table, it SHALL return a dict with keys `"total"`, `"by_outcome"`, `"avg_duration_seconds"`, and `"recent"`.

#### Scenario: build_proposal_stats_missing_db

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the returned dict contains key `"error"` with a string containing "not found"

#### Scenario: build_proposal_stats_valid_db

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a valid SQLite database with a `changes` table containing one row (`change_name="test-proposal"`, `outcome="success"`, `started_at="2025-01-01T00:00:00"`, `finished_at="2025-01-01T01:00:00"`)
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the returned dict has `"total"` equal to 1, `"by_outcome"` equal to `{"success": 1}`, and `"recent"` is a list of length 1

#### Scenario: build_proposal_stats_empty_db

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a valid SQLite database with a `changes` table containing zero rows
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the returned dict has `"total"` equal to 0, `"by_outcome"` equal to `{}`, and `"recent"` is an empty list

---

### Requirement: build_proposal_detail_basic
`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return detailed info for a single proposal including files, DB phases, and state. When the proposal directory does not exist in either the active or archive paths, it SHALL return a dict with key `"error"`.

#### Scenario: build_proposal_detail_not_found

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` contains no matching proposal directory (neither active nor archived)
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent-proposal")` is called
- **Then** the returned dict has key `"error"` containing "not found"

#### Scenario: build_proposal_detail_found_with_files

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/my-proposal/` exists with `proposal.md` containing `# My Proposal` and `clarify.md` containing `Some clarify text`
- **When** `_build_proposal_detail(":memory:", base_path, "my-proposal")` is called
- **Then** the returned dict has `"proposal_name"` equal to `"my-proposal"` and `"files"` dict containing keys `"proposal.md"` and `"clarify.md"`

---

### Requirement: build_pipeline_status_basic
`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys `"active_proposal"`, `"current_phase"`, `"phase_progress"`, `"design_gate_attempts"`, `"judge_feedback"`, `"queue"`, and `"daemon"`. When no daemon state exists, the `"daemon"` sub-dict SHALL have `"state"` equal to `"unknown"`.

#### Scenario: build_pipeline_status_empty_state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns an empty dict and `base_path` contains no changes directory
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** the returned dict has `"active_proposal"` equal to `None`, `"daemon"` dict with `"state"` equal to `"unknown"`, and `"queue"` as an empty list

---

### Requirement: health_check_db_probe
`_health_check(db_path)` SHALL perform a liveness probe against a SQLite database. On success, it SHALL return `{"status": "healthy", "db_records": <int>}`. On failure, it SHALL return `{"status": "unhealthy", "error": "<message>"}`.

#### Scenario: health_check_valid_db

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a valid SQLite database with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** the returned dict has `"status"` equal to `"healthy"` and `"db_records"` equal to 3

#### Scenario: health_check_missing_db

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a non-existent file
- **When** `_health_check(db_path)` is called
- **Then** the returned dict has `"status"` equal to `"unhealthy"` and `"error"` is a non-empty string

