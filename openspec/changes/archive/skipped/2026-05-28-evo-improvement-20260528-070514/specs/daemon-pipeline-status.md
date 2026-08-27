# daemon-pipeline-status

## ADDED Requirements

### Requirement: build-pipeline-status-structure
`_build_pipeline_status(db_path, base_path)` SHALL return a dictionary with the
keys `active_proposal`, `current_phase`, `phase_progress`, `queue`, and
`daemon`.  When no active proposal exists, `active_proposal` SHALL be `None`
and `phase_progress` SHALL be an empty list.

#### Scenario: no-active-proposal-returns-defaults

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state has no `current_change` and there are no directories with a `.phase_state` file
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result has `active_proposal` equal to `None`, `phase_progress` as an empty list, and `queue` as a list

#### Scenario: daemon-section-has-uptime

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state with `started_at` set to a recent ISO timestamp
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the `daemon` sub-dict has a key `uptime_seconds` that is a positive number

---

### Requirement: build-pipeline-status-active-proposal
When `_build_pipeline_status` detects an active proposal (matching
`current_change` in daemon state), it SHALL populate `active_proposal` with
the proposal name and include the proposal in the `queue` list with
`is_active == True`.

#### Scenario: active-proposal-populated-from-state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state has `current_change` set to `"my-change"`, and `openspec/changes/my-change/` exists with `proposal.md`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result has `active_proposal == "my-change"` and the `queue` list contains an entry with `name == "my-change"` and `is_active == True`

---

### Requirement: build-proposal-detail-missing
`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a
dictionary with an `"error"` key when the proposal directory does not exist in
either `openspec/changes/` or its `archive/` subdirectory.

#### Scenario: missing-proposal-returns-error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no directory named `nonexistent-change` in changes or archive
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-change")` is called
- **Then** the result contains an `"error"` key mentioning the proposal name

---

### Requirement: build-proposal-detail-files
`_build_proposal_detail` SHALL read diagnostic files (`proposal.md`,
`clarify.md`, `steward-review.md`, etc.) from the proposal directory and
include them (truncated to 8000 chars) in the `files` key of the returned
dictionary.

#### Scenario: reads-diagnostic-files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory with `proposal.md` and `clarify.md` files
- **When** `_build_proposal_detail(db_path, base_path, name)` is called
- **Then** the result `files` dict contains keys `"proposal.md"` and `"clarify.md"` with the file contents

---

### Requirement: build-proposal-detail-phase-state
`_build_proposal_detail` SHALL read `.phase_state` from the proposal directory
when it exists and include the parsed JSON in the `phase_state` key.

#### Scenario: reads-phase-state

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory with a `.phase_state` file containing `{"current_phase": "IMPLEMENT"}`
- **When** `_build_proposal_detail(db_path, base_path, name)` is called
- **Then** the result has `phase_state == {"current_phase": "IMPLEMENT"}`
