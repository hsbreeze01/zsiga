# daemon-pipeline-detail

Delta spec for `_build_pipeline_status(db_path, base_path)` and `_build_proposal_detail(db_path, base_path, proposal_name)`.

## ADDED Requirements

### Requirement: pipeline-status-structure

`_build_pipeline_status` SHALL return a dict with keys `active_proposal`, `current_phase`, `phase_progress`, `design_gate_attempts`, `judge_feedback`, `queue`, `daemon`. When no active proposal exists, `active_proposal` SHALL be `None` and `phase_progress` SHALL be an empty list.

#### Scenario: pipeline-status-no-active-proposal

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** a temporary database with no rows and a `base_path` with no change directories
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the returned dict has `active_proposal == None`, `phase_progress == []`, `queue == []`, and a `daemon` dict with `state == "unknown"`

#### Scenario: pipeline-status-with-active-proposal

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** a daemon state with `current_change == "test-change"`, a change directory `test-change/` containing `proposal.md` and `.phase_state` with `current_phase: "IMPLEMENT"`, and a temporary database with a matching row
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the returned dict has `active_proposal == "test-change"`, `current_phase == "IMPLEMENT"`, and `queue` contains an entry with `name == "test-change"` and `is_active == True`

### Requirement: pipeline-status-phase-progress

`_build_pipeline_status` SHALL build a `phase_progress` list with one entry per defined phase (`PROPOSAL_GATE`, `CLARIFY`, `ENRICH`, `DESIGN_GATE`, `IMPLEMENT`, `REVIEW`, `VERIFY`, `OPTIMIZE`, `REFLECT`, `DELIVER`). Each entry SHALL have `status` equal to `"PASS"`, `"DONE"`, `"RUNNING"`, or `"PENDING"`.

#### Scenario: pipeline-status-running-phase-entry

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** an active proposal whose `.phase_state` indicates `current_phase == "IMPLEMENT"` and no completed phases in the database
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `phase_progress` contains an entry with `phase == "IMPLEMENT"` and `status == "RUNNING"`, and entries for later phases have `status == "PENDING"`

### Requirement: proposal-detail-structure

`_build_proposal_detail` SHALL return a dict with keys `proposal_name`, `files`, `phases`, `phase_state`. When the proposal directory does not exist, it SHALL include an `error` key.

#### Scenario: proposal-detail-nonexistent-proposal

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a `base_path` with an `openspec/changes/` directory that contains no directory matching `proposal_name`
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** the returned dict has `proposal_name == "nonexistent"` and contains an `error` key

#### Scenario: proposal-detail-reads-files

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory `my-change/` containing `proposal.md` with content `# My Change` and `clarify.md` with content `## Details`
- **When** `_build_proposal_detail(db_path, base_path, "my-change")` is called
- **Then** the returned dict has `files["proposal.md"]` containing `"# My Change"` and `files["clarify.md"]` containing `"## Details"`

#### Scenario: proposal-detail-reads-phase-state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory with `.phase_state` containing `{"current_phase": "REVIEW", "started_at": "2026-05-30T01:00:00"}`
- **When** `_build_proposal_detail(db_path, base_path, <name>)` is called
- **Then** the returned dict has `phase_state["current_phase"] == "REVIEW"`

