# daemon-pipeline-detail

## ADDED Requirements

### Requirement: _build_pipeline_status SHALL return structured pipeline state

`_build_pipeline_status(db_path, base_path)` SHALL combine daemon state,
`.phase_state` files, and DB records into a single dict with keys
`active_proposal`, `current_phase`, `phase_progress`, `queue`, `daemon`.

#### Scenario: empty base path returns default structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` is mocked to return `{}`, `base_path` points to a temporary directory with an empty `openspec/changes/` directory, and `db_path` points to a non-existent file
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result SHALL contain `active_proposal == None`, `current_phase == None`, `phase_progress == []`, `queue == []`, and `daemon` as a dict

#### Scenario: proposal with phase state file is detected

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` is mocked to return `{"current_change": "test-change"}`, `base_path` contains `openspec/changes/test-change/proposal.md` and `openspec/changes/test-change/.phase_state` with content `{"current_phase": "IMPLEMENT"}`, and `db_path` points to a non-existent file
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result SHALL contain `active_proposal == "test-change"`, `current_phase == "IMPLEMENT"`, and `queue` SHALL be a list with at least one entry

---

### Requirement: _build_proposal_detail SHALL return files and phase data

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return
a dict with `proposal_name`, `files`, `phases`, `phase_state`.

#### Scenario: non-existent proposal returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` has no matching proposal directory (and no archive match)
- **When** `_build_proposal_detail(db_path, base_path, "ghost-proposal")` is called
- **Then** the result SHALL contain `"error"` key with a string mentioning the proposal name

#### Scenario: existing proposal reads files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` contains `openspec/changes/my-proposal/proposal.md` with content `# My Proposal` and no DB exists
- **When** `_build_proposal_detail(db_path, base_path, "my-proposal")` is called
- **Then** the result SHALL contain `proposal_name == "my-proposal"`, and `files["proposal.md"]` SHALL start with `"# My Proposal"`

---

### Requirement: _build_proposal_stats_json SHALL return aggregate stats

`_build_proposal_stats_json(db_path)` SHALL query the `changes` table and
return a dict with `total`, `by_outcome`, `avg_duration_seconds`, `recent`.

#### Scenario: missing database file returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a file that does not exist
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result SHALL contain `"error"` key

#### Scenario: valid database returns stats

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database at `db_path` with a `changes` table containing 2 rows (outcome `"success"` and `"fail"`)
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result SHALL contain `total == 2`, `by_outcome == {"success": 1, "fail": 1}`, and `"recent"` as a list of 2 items
