# daemon-pipeline-stats

Delta spec for pipeline status and proposal stats functions in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: _build_proposal_stats_json returns aggregate statistics

The system SHALL provide `_build_proposal_stats_json(db_path)` that
queries the `changes` table and returns a dict with keys `total`,
`by_outcome`, `avg_duration_seconds`, `recent`. On missing database it
MUST return `{"error": "..."}`.

#### Scenario: _build_proposal_stats_json returns stats for valid database

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table containing 2 rows:
  one with `outcome="success"` and one with `outcome="fail"`
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result has `total` equal to `2`
- **And** `by_outcome` has `{"success": 1, "fail": 1}`

#### Scenario: _build_proposal_stats_json returns error for missing database

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains key `error`

### Requirement: _build_proposal_detail returns detailed proposal info

The system SHALL provide `_build_proposal_detail(db_path, base_path,
proposal_name)` that reads files from the change directory and DB records.
When the proposal directory is not found, it MUST return a dict with
key `error`.

#### Scenario: _build_proposal_detail returns files and phase_state for existing proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory `my-change/` under `openspec/changes/`
  containing `proposal.md` and `.phase_state`
- **When** `_build_proposal_detail(":memory:", base_path, "my-change")` is called
- **Then** the result contains key `files`
- **And** `files` has key `proposal.md`

#### Scenario: _build_proposal_detail returns error for missing proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no change directory named `nonexistent` exists
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent")` is called
- **Then** the result contains key `error`

### Requirement: _build_pipeline_status returns phase-by-phase progress

The system SHALL provide `_build_pipeline_status(db_path, base_path)`
that returns a dict with `active_proposal`, `current_phase`,
`phase_progress`, `queue`, and `daemon` keys.

#### Scenario: _build_pipeline_status returns structure with daemon and queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"state": "running", "started_at": "<recent ISO>"}`
- **And** a valid `base_path` with an empty `openspec/changes/` directory
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** the result has keys `daemon`, `queue`, `phase_progress`
- **And** `queue` is a list
