# daemon-pipeline-status

Delta spec for `zsiga/daemon.py::_build_pipeline_status` and
`_build_proposal_detail`.

## ADDED Requirements

### Requirement: Pipeline Status Builder

`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys
`active_proposal`, `current_phase`, `phase_progress`, `design_gate_attempts`,
`judge_feedback`, `queue`, and `daemon`. It MUST handle missing daemon state,
missing database, and missing proposal directories gracefully.

#### Scenario: pipeline status with no daemon state and no proposals

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `daemon_state.json` does not exist and no change directories exist
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** `result["active_proposal"]` SHALL be `None`
- **And** `result["queue"]` SHALL be an empty list
- **And** `result["daemon"]["state"]` SHALL be `"unknown"`

#### Scenario: pipeline status with active proposal and phase state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `daemon_state.json` has `current_change` set to `"my-change"` and a
  change directory `my-change/` exists with a `.phase_state` file containing
  `{"current_phase": "IMPLEMENT"}`
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** `result["active_proposal"]` SHALL be `"my-change"`
- **And** `result["current_phase"]` SHALL be `"IMPLEMENT"`
- **And** `result["queue"]` SHALL contain an entry with `name` equal to `"my-change"` and `is_active` equal to `True`

#### Scenario: pipeline status daemon uptime is zero without started_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `daemon_state.json` exists but has no `started_at` key
- **When** `_build_pipeline_status(":memory:", base_path)` is called
- **Then** `result["daemon"]["uptime_seconds"]` SHALL be `0`

### Requirement: Proposal Detail Builder

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict
with `proposal_name`, `files`, `phases`, and `phase_state`. It MUST return an
`error` key when the proposal directory is not found.

#### Scenario: proposal detail for non-existent proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no change directory exists for the proposal name
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent-change")` is called
- **Then** `result["error"]` SHALL contain a message indicating the proposal was not found

#### Scenario: proposal detail reads proposal.md content

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory with `proposal.md` containing text content
- **When** `_build_proposal_detail(":memory:", base_path, name)` is called
- **Then** `result["files"]["proposal.md"]` SHALL contain the file content (truncated to 8000 chars)

#### Scenario: proposal detail reads phase state

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory with `.phase_state` containing valid JSON
- **When** `_build_proposal_detail(":memory:", base_path, name)` is called
- **Then** `result["phase_state"]` SHALL equal the parsed JSON content

#### Scenario: proposal detail reads spec files from specs directory

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory with `specs/feature.md` containing spec text
- **When** `_build_proposal_detail(":memory:", base_path, name)` is called
- **Then** `result["files"]["specs/feature.md"]` SHALL contain the spec file content
