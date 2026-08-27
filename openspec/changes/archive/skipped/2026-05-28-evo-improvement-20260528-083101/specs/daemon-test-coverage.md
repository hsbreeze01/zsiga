# daemon-test-coverage

Delta spec for adding unit test coverage to `zsiga/daemon.py`.

This spec covers functions **not** already tested by
`tests/test_daemon_state.py` (10 tests for `_write_daemon_state`),
`tests/test_daemon_scheduling.py` (12 tests for `daemon_loop` scheduling),
and `tests/test_daemon_cycle_resilience.py` (7 tests for cycle error handling).

## ADDED Requirements

### Requirement: Tool Function Path Tests

The test file `tests/test_daemon.py` SHALL contain tests verifying the
behaviour of `_lock_path`, `_daemon_state_path`, and `_read_daemon_state`.

#### Scenario: lock_path_returns_pid_lock_under_data_dir

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid`
- **And** the `data/` directory has been created

#### Scenario: daemon_state_path_returns_json_under_data_dir

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json`

#### Scenario: read_daemon_state_returns_existing_json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file exists containing `{"pid": 42, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 42, "state": "running"}`

#### Scenario: read_daemon_state_returns_empty_on_missing_file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no daemon state file exists
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: read_daemon_state_returns_empty_on_corrupt_json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file exists containing invalid JSON `{broken`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

### Requirement: Uptime Computation Tests

The test file SHALL contain tests verifying `_compute_uptime_seconds`.

#### Scenario: compute_uptime_with_valid_timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** a valid ISO timestamp 60 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the returned value is approximately 60.0 (within 5.0 seconds tolerance)

#### Scenario: compute_uptime_returns_none_for_none_input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** it returns `None`

#### Scenario: compute_uptime_returns_none_for_empty_string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string
- **When** `_compute_uptime_seconds("")` is called
- **Then** it returns `None`

#### Scenario: compute_uptime_returns_none_for_invalid_string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** it returns `None`

### Requirement: Proposal Queue Scanning Tests

The test file SHALL contain tests verifying `_scan_proposal_queue`.

#### Scenario: scan_empty_directory_returns_empty_list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** an empty `changes_dir`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: scan_nonexistent_directory_returns_empty_list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a non-existent path
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: scan_extracts_summary_from_proposal_heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory containing `proposal.md` with first `# ` heading `"Fix login bug"`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `summary` equal to `"Fix login bug"`

#### Scenario: scan_skips_dirs_without_proposal_md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory without `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry is excluded from the returned list

#### Scenario: scan_detects_clarify_phase_by_default

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` but no `clarify.md` or `specs/`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase` equal to `"CLARIFY"`

#### Scenario: scan_detects_enrich_phase_with_clarify_md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` and `clarify.md` (but no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase` equal to `"ENRICH"`

#### Scenario: scan_detects_implement_phase_with_specs_dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md`, `clarify.md`, and `specs/some.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase` equal to `"IMPLEMENT"`

#### Scenario: scan_detects_paused_via_dot_paused_file

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` and a `.paused` marker file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused` equal to `True`
- **And** `lifecycle` equal to `"paused"`

### Requirement: Lock Management Tests

The test file SHALL contain tests verifying `acquire_lock` and `release_lock`.

#### Scenario: acquire_lock_creates_lock_file

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `acquire_lock()` is called
- **Then** it returns a tuple `(fd, True)`
- **And** the lock file at `_lock_path()` exists and contains the current PID

#### Scenario: release_lock_removes_lock_file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock has been acquired via `acquire_lock()`
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

### Requirement: Status Builder Tests

The test file SHALL contain tests verifying `_build_status_json` and
`_build_metrics_json`.

#### Scenario: build_status_json_contains_daemon_and_queue_keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` is mocked to return `{"state": "running", "cycle": 1}`
- **And** `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON with top-level keys `"daemon"` and `"queue"`

#### Scenario: build_status_json_daemon_section_has_required_fields

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` is mocked to return `{"state": "running", "cycle": 1, "pid": 99, "current_change": "fix-x", "current_phase": "enrich", "current_project": "proj", "last_heartbeat": "2025-01-01T00:00:00", "started_at": "2025-01-01T00:00:00"}`
- **And** `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_status_json()` is called
- **Then** `result["daemon"]` contains keys `"pid"`, `"state"`, `"cycle"`, `"current_change"`, `"current_phase"`, `"current_project"`, `"heartbeat"`, `"uptime_seconds"`

#### Scenario: build_metrics_json_returns_valid_json

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` is mocked to return `{"summary": {"total": 5}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON with key `"summary"` containing `{"total": 5}`

#### Scenario: build_metrics_json_returns_error_on_exception

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` is mocked to raise `RuntimeError("db down")`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON with key `"error"` containing `"db down"`

### Requirement: Pipeline Status Builder Tests

The test file SHALL contain tests verifying `_build_pipeline_status`.

#### Scenario: pipeline_status_returns_required_top_level_keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` is mocked to return `{}`
- **And** `base_path` points to a temporary directory with no `openspec/changes/`
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** the returned dict contains keys `"active_proposal"`, `"current_phase"`, `"phase_progress"`, `"queue"`, `"daemon"`

#### Scenario: pipeline_status_daemon_uptime_zero_when_no_started_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` is mocked to return `{}`
- **And** `base_path` points to a temporary directory with no `openspec/changes/`
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** `result["daemon"]["uptime_seconds"]` is `0`

#### Scenario: pipeline_status_detects_active_proposal_from_daemon_state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"current_change": "my-change"}`
- **And** `base_path/openspec/changes/my-change/proposal.md` exists
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** `result["active_proposal"]` equals `"my-change"`

### Requirement: Proposal Detail Builder Tests

The test file SHALL contain tests verifying `_build_proposal_detail`.

#### Scenario: proposal_detail_returns_error_for_unknown_proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` has no matching proposal directory
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent")` is called
- **Then** the returned dict has key `"error"` containing `"not found"` (case-insensitive)

#### Scenario: proposal_detail_reads_diagnostic_files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory with `proposal.md` content `"# Test Proposal"`
- **When** `_build_proposal_detail(":memory:", base_path, "test-change")` is called
- **Then** `result["files"]["proposal.md"]` contains `"# Test Proposal"`

### Requirement: Health Check Tests

The test file SHALL contain tests verifying `_health_check`.

#### Scenario: health_check_healthy_with_valid_db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 5 rows
- **When** `_health_check(db_path)` is called
- **Then** it returns `{"status": "healthy", "db_records": 5}`

#### Scenario: health_check_unhealthy_on_missing_db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a non-existent file
- **When** `_health_check(db_path)` is called
- **Then** it returns a dict with `"status"` equal to `"unhealthy"`

### Requirement: Test File Quality Gates

The test file `tests/test_daemon.py` SHALL satisfy mechanical quality checks.

#### Scenario: test_file_exists

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the change has been implemented
- **When** checking for `tests/test_daemon.py`
- **Then** the file exists

#### Scenario: test_file_contains_required_function_names

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the change has been implemented
- **When** scanning `tests/test_daemon.py` for test function names
- **Then** it contains functions named `test__lock_path`, `test__daemon_state_path`, and `test__read_daemon_state`

#### Scenario: test_file_has_minimum_test_count

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the change has been implemented
- **When** counting `def test_` declarations in `tests/test_daemon.py`
- **Then** the count is at least 20

#### Scenario: pytest_exits_zero

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the change has been implemented
- **When** running `python -m pytest tests/test_daemon.py`
- **Then** the exit code is 0
