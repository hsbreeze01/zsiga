# daemon-pipeline-detail

## ADDED Requirements

### REQ-PD-01: Pipeline status builder

`_build_pipeline_status` SHALL combine daemon state, phase state files, and
database records to produce a detailed status dict. The result MUST contain keys:
`active_proposal`, `current_phase`, `phase_progress`, `queue`, `daemon`.

When the changes directory does not exist, the `queue` SHALL be empty and
`active_proposal` SHALL be `None`.

#### Scenario: pipeline-status-no-changes-dir

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** no daemon state and a `base_path` with no `openspec/changes/` directory
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** returns a dict with `active_proposal=None`, `queue=[]`, and
  `phase_progress=[]`

#### Scenario: pipeline-status-detects-active-proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state with `current_change="fix-logging"` and a changes directory
  containing a subdirectory `fix-logging` with `proposal.md`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `active_proposal` is `"fix-logging"` and the queue entry for
  `fix-logging` has `is_active=True`

#### Scenario: pipeline-status-sorts-entries

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** a changes directory with proposal subdirectories `alpha` and `beta`
  (sorted order) and no active proposal in daemon state
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the queue contains entries for `alpha` and `beta` in sorted order

### REQ-PD-02: Proposal detail builder

`_build_proposal_detail` SHALL return a dict with keys `proposal_name`, `files`,
`phases`, `phase_state`. When the proposal directory does not exist, the result
SHALL contain an `"error"` key. When the directory exists, `files` SHALL contain
the content of known diagnostic files (`proposal.md`, `clarify.md`, etc.) up to
8000 characters each.

#### Scenario: proposal-detail-missing-name

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a `base_path` with no matching proposal directory
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-proposal")`
  is called
- **Then** returns a dict with key `"error"` containing a descriptive message

#### Scenario: proposal-detail-reads-files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory containing `proposal.md` and `clarify.md`
- **When** `_build_proposal_detail(db_path, base_path, proposal_name)` is called
- **Then** the `files` dict contains keys `"proposal.md"` and `"clarify.md"` with
  the respective file contents

#### Scenario: proposal-detail-reads-phase-state

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory containing `.phase_state` with valid JSON
- **When** `_build_proposal_detail(db_path, base_path, proposal_name)` is called
- **Then** the `phase_state` key contains the parsed JSON object

### REQ-PD-03: Proposal stats JSON builder

`_build_proposal_stats_json` SHALL query the changes table and return aggregate
statistics. When the database file does not exist, it SHALL return a dict with an
`"error"` key. When the database exists but has no `changes` table, it SHALL also
return an `"error"` key.

#### Scenario: proposal-stats-missing-db

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a `db_path` to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** returns a dict with key `"error"` containing "not found" or similar message

#### Scenario: proposal-stats-empty-db

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a valid SQLite database with no `changes` table
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** returns a dict with key `"error"`
