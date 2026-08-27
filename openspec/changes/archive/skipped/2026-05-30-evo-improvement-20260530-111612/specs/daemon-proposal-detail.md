# daemon-proposal-detail

## ADDED Requirements

### Requirement: Build proposal detail from DB and filesystem

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a
dict with keys `"proposal_name"`, `"files"`, `"phases"`, `"phase_state"`.
When the proposal directory does not exist (even after searching archives), it
SHALL include `"error"`.

#### Scenario: Non-existent proposal returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no directory for the proposal name exists in `changes/` or `archive/`
- **When** `_build_proposal_detail(":memory:", base_path, "nonexistent")` is called
- **Then** the result contains `"error"` with a string mentioning the proposal name

#### Scenario: Existing proposal returns files and phases

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory exists with `proposal.md` containing `# My Proposal`
- **When** `_build_proposal_detail(":memory:", base_path, "<dir_name>")` is called
- **Then** the result contains `"files"` dict with key `"proposal.md"` and its value starts with `# My Proposal`

#### Scenario: Phase state file is parsed when present

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory exists with a `.phase_state` file containing `{"current_phase": "IMPLEMENT"}`
- **When** `_build_proposal_detail(":memory:", base_path, "<dir_name>")` is called
- **Then** the result's `"phase_state"` equals `{"current_phase": "IMPLEMENT"}`

---

### Requirement: Build proposal statistics from DB

`_build_proposal_stats_json(db_path)` SHALL return a dict with keys
`"total"`, `"by_outcome"`, `"avg_duration_seconds"`, `"recent"`.  When the
database file does not exist, it SHALL return `{"error": "<message>"}`.

#### Scenario: Missing database file returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains `"error"` with a message about file not found

#### Scenario: Database with records returns stats

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database at `db_path` with a `changes` table containing 2 rows of outcome `"success"`
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains `"total": 2` and `"by_outcome": {"success": 2}`

#### Scenario: Database without changes table returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database at `db_path` with no `changes` table
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains `"error"` mentioning the changes table

---

### Requirement: Detect proposal phase via transport

`_detect_proposal_phase(name)` SHALL return one of `"CLARIFY"`, `"ENRICH"`,
`"IMPLEMENT"`, `"REVIEW"` based on which output files exist.  On any exception
it SHALL default to `"CLARIFY"`.

#### Scenario: Exception during detection returns CLARIFY

- **testable**: true
- **target**: zsiga/daemon.py::_detect_proposal_phase
- **Given** `load_config()` raises an exception
- **When** `_detect_proposal_phase("any-name")` is called
- **Then** it returns `"CLARIFY"`
