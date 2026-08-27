# daemon-status-pipeline-tests

## ADDED Requirements

### Requirement: Status and metrics JSON builders
`_build_status_json()` SHALL return a valid JSON string containing `"daemon"`
and `"queue"` keys. `_build_metrics_json()` SHALL return a valid JSON string;
on error it MUST return `{"error": "<message>"}`.

#### Scenario: status json contains daemon and queue keys
- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** daemon state file contains `{"pid": 42, "state": "running"}`
- **When** `_build_status_json()` is called
- **Then** the result is valid JSON with top-level keys `"daemon"` and `"queue"`

#### Scenario: metrics json returns error on failure
- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** the `metrics.dashboard.compute_stats` import raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the result is a JSON string containing an `"error"` key

### Requirement: Health check against SQLite
`_health_check(db_path)` SHALL return `{"status": "healthy", "db_records": N}`
when the database is reachable, or `{"status": "unhealthy", "error": "<msg>"}`
on any failure.

#### Scenario: healthy database returns record count
- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database with a `changes` table containing 5 rows
- **When** `_health_check(db_path)` is called
- **Then** the result equals `{"status": "healthy", "db_records": 5}`

#### Scenario: missing database returns unhealthy
- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** the database file does not exist
- **When** `_health_check("/nonexistent/path.db")` is called
- **Then** the result has `"status"` equal to `"unhealthy"` and a non-empty `"error"` key

### Requirement: Pipeline status builder
`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys
`active_proposal`, `current_phase`, `phase_progress`, `queue`, and `daemon`.
When no active proposal exists, `active_proposal` MUST be `None`.

#### Scenario: no active proposal returns none
- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** an empty changes directory and no daemon state
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["active_proposal"]` is `None` and `result["queue"]` is `[]`

#### Scenario: proposal directory with phase state marks active
- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state has `current_change` set to `"my-change"` and the proposal directory exists with `proposal.md`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["active_proposal"]` is `"my-change"`

### Requirement: Proposal detail builder
`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict
with keys `proposal_name`, `files`, `phases`, `phase_state`. When the proposal
directory does not exist, it MUST include an `"error"` key.

#### Scenario: non-existent proposal returns error
- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no proposal directory matching the name exists
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** `result["error"]` contains `"not found"` text

#### Scenario: existing proposal returns files dict
- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory with `proposal.md` and `clarify.md`
- **When** `_build_proposal_detail(db_path, base_path, "my-change")` is called
- **Then** `result["files"]` contains `"proposal.md"` and `"clarify.md"` keys with string content
