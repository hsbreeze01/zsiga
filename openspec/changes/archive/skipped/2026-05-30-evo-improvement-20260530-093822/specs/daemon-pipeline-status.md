# daemon-pipeline-status.md

## ADDED Requirements

### Requirement: _build_pipeline_status returns structured dict

`_build_pipeline_status(db_path, base_path)` SHALL return a dict containing
keys `"active_proposal"`, `"current_phase"`, `"phase_progress"`, `"queue"`,
and `"daemon"`.

#### Scenario: empty paths return default structure

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status

- **Given** `db_path` points to a non-existent database file and `base_path` has no `openspec/changes/` directory
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result is a dict with keys `"active_proposal"` (None), `"current_phase"` (None), `"phase_progress"` ([]), `"queue"` ([]), `"daemon"` (dict with `"state"`)

### Requirement: _build_proposal_detail returns structured dict

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict
with keys `"proposal_name"`, `"files"`, `"phases"`, `"phase_state"`.

#### Scenario: non-existent proposal returns error dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail

- **Given** `base_path` has no matching proposal directory (neither active nor archived)
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-proposal")` is called
- **Then** the result dict contains key `"error"` with a string mentioning the proposal name

#### Scenario: existing proposal returns files dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail

- **Given** `base_path/openspec/changes/existing-proposal/` exists with `proposal.md` content `"# My Proposal"`
- **When** `_build_proposal_detail(db_path, base_path, "existing-proposal")` is called
- **Then** the result dict's `"files"` key contains `"proposal.md"` with the file content, and `"proposal_name"` equals `"existing-proposal"`

