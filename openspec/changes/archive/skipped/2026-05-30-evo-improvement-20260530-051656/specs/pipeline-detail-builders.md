# pipeline-detail-builders

## ADDED Requirements

### Requirement: _build_pipeline_status SHALL return dict with expected structure

`_build_pipeline_status(db_path, base_path)` SHALL return a dict with
keys `active_proposal`, `current_phase`, `phase_progress`, `queue`,
`daemon`, `design_gate_attempts`, and `judge_feedback`.

#### Scenario: _build_pipeline_status returns dict with all required keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"state": "running", "cycle": 1,
  "started_at": "2025-01-01T00:00:00"}` and `base_path` points to a directory
  with no `openspec/changes/` subdirectory, and `db_path` is a non-existent path
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result SHALL be a dict containing keys `active_proposal`,
  `current_phase`, `phase_progress`, `queue`, `daemon`

#### Scenario: _build_pipeline_status daemon key includes state and cycle

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"state": "paused", "cycle": 7,
  "started_at": "2025-01-01T00:00:00"}`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["daemon"]["state"]` SHALL equal `"paused"` and
  `result["daemon"]["cycle"]` SHALL equal `7`

### Requirement: _build_proposal_detail SHALL return dict with proposal info

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return
a dict with keys `proposal_name`, `files`, `phases`, `phase_state`. If
the proposal directory is not found, it SHALL include an `error` key.

#### Scenario: _build_proposal_detail returns error for unknown proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` points to an empty temporary directory and
  `proposal_name` is `"nonexistent-change"`
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent-change")` is called
- **Then** the result SHALL be a dict with `proposal_name == "nonexistent-change"`
  and an `"error"` key containing a not-found message

#### Scenario: _build_proposal_detail reads files from change directory

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` contains `openspec/changes/my-change/proposal.md`
  with content `# Hello World`
- **When** `_build_proposal_detail(":memory:", base_path, "my-change")` is called
- **Then** the result's `files` dict SHALL contain key `"proposal.md"` with
  value starting with `# Hello World`

#### Scenario: _build_proposal_detail includes phases from DB when available

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** an in-memory SQLite database with a `changes` table containing
  one row with `change_name="db-change"` and `phases_json='[{"phase":"CLARIFY","outcome":"success"}]'`,
  and `base_path` contains `openspec/changes/db-change/proposal.md`
- **When** `_build_proposal_detail(db_path, base_path, "db-change")` is called
- **Then** the result's `phases` SHALL be a list containing at least one
  entry with `phase == "CLARIFY"`
