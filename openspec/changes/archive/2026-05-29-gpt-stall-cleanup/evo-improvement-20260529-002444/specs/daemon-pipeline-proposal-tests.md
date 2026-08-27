# daemon-pipeline-proposal-tests

## ADDED Requirements

### Requirement: _build_pipeline_status SHALL assemble phase-by-phase progress

`_build_pipeline_status()` SHALL return a dict containing `active_proposal`,
`current_phase`, `phase_progress`, `queue`, and `daemon` keys. It SHALL
gracefully handle missing daemon state, missing database, and missing
`.phase_state` files.

#### Scenario: pipeline_status with no daemon state and no changes dir

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state is empty, `base_path` points to a temp dir with no `openspec/changes/`, and `db_path` is a valid SQLite database with an empty `changes` table
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result contains keys `active_proposal`, `current_phase`, `phase_progress`, `queue`, `daemon`
- **And** `active_proposal` is `None`
- **And** `queue` is `[]`

#### Scenario: pipeline_status with active proposal in changes dir

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** daemon state has `current_change="fix-foo"`, `base_path/openspec/changes/fix-foo/proposal.md` exists, and `.phase_state` contains `{"current_phase": "IMPLEMENT"}`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `active_proposal` equals `"fix-foo"`
- **And** `current_phase` equals `"IMPLEMENT"`
- **And** `queue` contains an entry with `name="fix-foo"` and `is_active=True`

#### Scenario: pipeline_status handles missing database gracefully

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `db_path` points to a non-existent file
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result is still a valid dict (no exception raised)
- **And** `phase_progress` is `[]`

---

### Requirement: _build_proposal_detail SHALL read proposal files and DB phases

`_build_proposal_detail()` SHALL return a dict with `proposal_name`, `files`,
`phases`, and `phase_state`. It SHALL read diagnostic files from the change
directory and phases from the SQLite database. When the proposal directory
does not exist, it SHALL include an `"error"` key.

#### Scenario: proposal_detail reads existing proposal files

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/fix-bar/proposal.md` contains `# Fix Bar` and `clarify.md` contains `clarification text`
- **When** `_build_proposal_detail(db_path, base_path, "fix-bar")` is called
- **Then** `result["files"]` contains key `"proposal.md"` with value starting with `"# Fix Bar"`
- **And** `result["files"]` contains key `"clarify.md"`

#### Scenario: proposal_detail returns error for missing proposal

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no sub-directory named `nonexistent` exists under `openspec/changes/` or its `archive/`
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** `result["error"]` contains the string `"not found"` (case-insensitive)

#### Scenario: proposal_detail reads phase_state file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/fix-baz/.phase_state` contains `{"current_phase": "REVIEW"}`
- **When** `_build_proposal_detail(db_path, base_path, "fix-baz")` is called
- **Then** `result["phase_state"]` equals `{"current_phase": "REVIEW"}`

#### Scenario: proposal_detail reads phases_json from database

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** the `changes` table has a row with `change_name="fix-qux"` and `phases_json='[{"phase":"IMPLEMENT","outcome":"success","seconds_used":42}]'`
- **When** `_build_proposal_detail(db_path, base_path, "fix-qux")` is called
- **Then** `result["phases"]` is a list with one entry where `phase == "IMPLEMENT"`

