# daemon-proposal-detail

## ADDED Requirements

### Requirement: Build proposal detail with files and DB record

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return
a dict with keys `proposal_name`, `files`, `phases`, `phase_state`.
When the proposal directory does not exist, it SHALL return a dict with
an `"error"` key describing the missing directory.

#### Scenario: Returns error when proposal directory not found

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` has no `openspec/changes/missing-proposal/` directory
  and no matching archive entry
- **When** `_build_proposal_detail(db_path, base_path, "missing-proposal")` is called
- **Then** the result has key `"error"` containing the string
  `"Proposal directory not found"` and `proposal_name` equals
  `"missing-proposal"`

#### Scenario: Reads proposal.md and clarify.md from change dir

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/test-proposal/` contains
  `proposal.md` with content `"# Test Proposal"` and `clarify.md` with
  content `"## Needs"`
- **When** `_build_proposal_detail(":memory:", base_path, "test-proposal")`
  is called
- **Then** the result's `"files"` dict contains keys `"proposal.md"` and
  `"clarify.md"` with the respective content

#### Scenario: Reads phase_state from .phase_state file

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** the proposal directory contains `.phase_state` with content
  `{"current_phase": "IMPLEMENT"}`
- **When** `_build_proposal_detail(":memory:", base_path, "test-proposal")`
  is called
- **Then** the result's `"phase_state"` dict has `"current_phase"` equal
  to `"IMPLEMENT"`

#### Scenario: Reads spec files from specs/ subdirectory

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** the proposal directory contains `specs/my-spec.md` with
  content `"## Added"`
- **When** `_build_proposal_detail(":memory:", base_path, "test-proposal")`
  is called
- **Then** the result's `"files"` dict contains key `"specs/my-spec.md"`
  with content `"## Added"`

---

### Requirement: Build proposal stats from DB

`_build_proposal_stats_json(db_path)` SHALL return a dict with keys
`total`, `by_outcome`, `avg_duration_seconds`, `recent` on success, or
a dict with key `"error"` on failure.

#### Scenario: Returns error for non-existent database file

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a file that does not exist
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result has key `"error"` containing `"Database file not found"`

#### Scenario: Returns error when changes table missing

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to an empty SQLite database (no tables)
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result has key `"error"` containing `"changes table does not exist"`

#### Scenario: Returns aggregate stats from populated DB

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a SQLite database with a `changes` table
  containing 2 rows: one `success` and one `fail`
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result has `"total"` equal to `2` and `"by_outcome"` equal
  to `{"success": 1, "fail": 1}`

---

### Requirement: Health check probes database liveness

`_health_check(db_path)` SHALL return `{"status": "healthy",
"db_records": <int>}` when the database is reachable, or
`{"status": "unhealthy", "error": "<msg>"}` on any failure.

#### Scenario: Returns unhealthy for missing database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a file that does not exist
- **When** `_health_check(db_path)` is called
- **Then** the result has `"status"` equal to `"unhealthy"` and key
  `"error"` present

#### Scenario: Returns healthy with record count

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a SQLite database with a `changes` table
  containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** the result has `"status"` equal to `"healthy"` and
  `"db_records"` equal to `3`
