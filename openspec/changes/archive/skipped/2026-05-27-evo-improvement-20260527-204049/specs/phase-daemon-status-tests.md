# phase-daemon-status-tests.md

## ADDED Requirements

### Requirement: daemon-status-builder-tests
The test suite SHALL verify that `_build_current_json()`, `_health_check()`, `_build_proposal_stats_json()`, `_build_pipeline_status()`, and `_build_proposal_detail()` produce correctly structured responses for both healthy and error conditions.

Note: `_build_status_json()` is already extensively tested in `tests/test_dashboard_api.py::TestBuildStatusJson` (7 tests). The scenarios below focus on functions NOT covered elsewhere.

#### Scenario: health-check-healthy-db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a temporary SQLite database with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called with the path to this database
- **Then** the result SHALL be `{"status": "healthy", "db_records": 3}`

#### Scenario: health-check-missing-db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a database path that does not exist on disk
- **When** `_health_check(db_path)` is called
- **Then** the result SHALL have `"status"` equal to `"unhealthy"` and SHALL contain an `"error"` key with a non-empty string

#### Scenario: proposal-stats-json-with-data

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a temporary SQLite database with a `changes` table containing rows with outcomes `"success"` and `"fail"`
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result SHALL contain `total` (int > 0), `by_outcome` (dict with `"success"` and `"fail"` keys), and `recent` (list)

#### Scenario: proposal-stats-json-missing-db

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a database path that does not exist
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result SHALL contain `"error"` key with value starting with `"Database file not found"`

#### Scenario: build-current-json-structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state()` returns `{"pid": 42, "state": "running", "cycle": 5, "started_at": "2025-01-01T00:00:00"}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_current_json()` is called (monkeypatched)
- **Then** the result SHALL be a valid JSON string with top-level keys `"daemon"`, `"current"`, and `"queue"`, and `daemon.pid` SHALL be 42

#### Scenario: build-current-json-phase-progress

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state()` returns `{"current_phase": "IMPLEMENT", "pid": 1, "state": "running", "started_at": "2025-01-01T00:00:00"}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_current_json()` is called (monkeypatched)
- **Then** the parsed JSON's `current.phase_progress` SHALL be a list of 6 entries where `"IMPLEMENT"` has `status` `"active"`, phases before it have `status` `"done"`, and phases after it have `status` `"pending"`

#### Scenario: build-current-json-phase-progress-without-phase

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state()` returns `{"pid": 1, "state": "running", "started_at": "2025-01-01T00:00:00"}` with no `current_phase` key and `_scan_proposal_queue()` returns `[]`
- **When** `_build_current_json()` is called (monkeypatched)
- **Then** the parsed JSON's `current.phase_progress` SHALL be a list of 6 entries where no entry has `status` `"active"`

#### Scenario: build-pipeline-status-no-active-proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state()` returns `{}` (no current_change), `db_path` points to a temporary SQLite database with a `changes` table, and `base_path` points to a temporary directory with an empty `openspec/changes/` directory
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result SHALL contain `active_proposal` as `None`, `current_phase` as `None`, `phase_progress` as an empty list, and `daemon` dict with `state` `"unknown"`

#### Scenario: build-pipeline-status-with-active-proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state()` returns `{"current_change": "test-change", "started_at": "2025-01-01T00:00:00"}`, the changes dir contains `test-change/proposal.md`, a temporary SQLite DB has a `changes` table with `phases_json` containing `[{"phase": "CLARIFY", "outcome": "success", "seconds_used": 10}]`, and `test-change/.phase_state` contains `{"current_phase": "ENRICH"}`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result SHALL have `active_proposal` as `"test-change"`, `current_phase` as `"ENRICH"`, and `phase_progress` SHALL include an entry for CLARIFY with status `"PASS"` and an entry for ENRICH with status `"RUNNING"`

#### Scenario: build-proposal-detail-missing-proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a base_path with `openspec/changes/` containing no subdirectory matching `nonexistent-change`
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-change")` is called
- **Then** the result SHALL contain `proposal_name` as `"nonexistent-change"` and SHALL have an `"error"` key containing the text `"Proposal directory not found"`

#### Scenario: build-proposal-detail-reads-files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a base_path with `openspec/changes/test-proposal/` containing `proposal.md` with text `"# Test Proposal"` and `clarify.md` with text `"# Clarify"`, and a temporary SQLite DB with a `changes` table having a row for `test-proposal`
- **When** `_build_proposal_detail(db_path, base_path, "test-proposal")` is called
- **Then** the result SHALL contain `files` dict with keys `"proposal.md"` and `"clarify.md"`, and `proposal_name` SHALL be `"test-proposal"`

#### Scenario: build-proposal-detail-reads-phase-state

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a base_path with `openspec/changes/test-proposal/` containing `proposal.md` and `.phase_state` with content `{"current_phase": "IMPLEMENT", "started_at": "2025-01-01T00:00:00"}`
- **When** `_build_proposal_detail(db_path, base_path, "test-proposal")` is called
- **Then** the result SHALL contain `phase_state` dict with `current_phase` as `"IMPLEMENT"`
