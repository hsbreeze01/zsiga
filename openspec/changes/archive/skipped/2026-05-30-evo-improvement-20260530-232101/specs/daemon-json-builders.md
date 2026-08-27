# daemon-json-builders

## ADDED Requirements

### Requirement: _build_pipeline_status SHALL return structured pipeline state

`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys
`active_proposal`, `current_phase`, `phase_progress`, `design_gate_attempts`,
`judge_feedback`, `queue`, and `daemon`. When no active proposal exists,
`active_proposal` SHALL be `None` and `phase_progress` SHALL be an empty list.

#### Scenario: no changes directory returns empty queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status

- **Given** `base_path` points to a directory with no `openspec/changes/` subdirectory
- **And** `db_path` points to a non-existent SQLite file
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["queue"]` is `[]`
- **And** `result["active_proposal"]` is `None`
- **And** `result["phase_progress"]` is `[]`

#### Scenario: proposal with phase_state identified as active

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status

- **Given** `base_path/openspec/changes/my-change/proposal.md` exists
- **And** `base_path/openspec/changes/my-change/.phase_state` contains `{"current_phase": "IMPLEMENT"}`
- **And** daemon state has `current_change` set to `"my-change"`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["active_proposal"]` equals `"my-change"`
- **And** `result["current_phase"]` equals `"IMPLEMENT"`

#### Scenario: daemon section contains state and cycle from daemon_state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status

- **Given** `daemon_state.json` contains `{"state": "running", "cycle": 7, "started_at": "<recent ISO>"}`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["daemon"]["state"]` equals `"running"`
- **And** `result["daemon"]["cycle"]` equals `7`

### Requirement: _build_proposal_detail SHALL return proposal files and phases

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict
with `proposal_name`, `files`, `phases`, and `phase_state` keys. It SHALL read
diagnostic files from the change directory and phase history from the database.

#### Scenario: missing proposal returns error dict

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail

- **Given** `base_path/openspec/changes/` contains no directory named `nonexistent`
- **And** no archive directory matches
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** `result["error"]` contains the string `"not found"` (case-insensitive)
- **And** `result["proposal_name"]` equals `"nonexistent"`

#### Scenario: existing proposal reads diagnostic files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail

- **Given** `base_path/openspec/changes/my-change/proposal.md` contains `"# My Proposal"`
- **And** `base_path/openspec/changes/my-change/clarify.md` contains `"# Clarification"`
- **When** `_build_proposal_detail(db_path, base_path, "my-change")` is called
- **Then** `result["files"]["proposal.md"]` equals `"# My Proposal"`
- **And** `result["files"]["clarify.md"]` equals `"# Clarification"`
- **And** `result["change_dir"]` is a string containing `"my-change"`

#### Scenario: proposal reads phase_state file

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail

- **Given** `base_path/openspec/changes/my-change/.phase_state` contains `{"current_phase": "REVIEW"}`
- **When** `_build_proposal_detail(db_path, base_path, "my-change")` is called
- **Then** `result["phase_state"]` equals `{"current_phase": "REVIEW"}`

### Requirement: _build_metrics_json SHALL return valid JSON payload

`_build_metrics_json()` SHALL return a JSON string. When the metrics module is
available, it SHALL contain `summary` and `phases` keys. When an exception
occurs, it SHALL return `{"error": "<message>"}` instead of raising.

#### Scenario: exception during metrics computation returns error JSON

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json

- **Given** `zsiga.metrics.dashboard.compute_stats` raises `ImportError`
- **When** `_build_metrics_json()` is called
- **Then** the result is valid JSON parseable by `json.loads`
- **And** the parsed dict contains an `"error"` key
