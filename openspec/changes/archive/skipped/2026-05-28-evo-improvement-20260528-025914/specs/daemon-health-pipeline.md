# daemon-health-pipeline — Health Check, Proposal Stats & Pipeline Status

## ADDED Requirements

### Requirement: SQLite health check

`_health_check(db_path)` SHALL connect to the SQLite database at `db_path` and query the
`changes` table count. On success it returns `{"status": "healthy", "db_records": <int>}`.
On any failure (missing file, missing table, connection error) it returns
`{"status": "unhealthy", "error": "<message>"}`.

#### Scenario: healthy database returns record count

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database exists at `db_path` with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "healthy", "db_records": 3}`

#### Scenario: non-existent database returns unhealthy

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_health_check
- **Given** no file exists at `db_path`
- **When** `_health_check(db_path)` is called
- **Then** the result has `"status"` equal to `"unhealthy"`
- **And** the result contains an `"error"` key with a non-empty string

---

### Requirement: Proposal aggregate statistics

`_build_proposal_stats_json(db_path)` SHALL query the `changes` table and return a `dict`
with keys `total`, `by_outcome`, `avg_duration_seconds`, and `recent`. If the database file
does not exist, it SHALL return `{"error": "<message>"}`.

#### Scenario: non-existent database returns error dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** no file exists at `db_path`
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains the key `"error"`

#### Scenario: database with single successful change

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table containing one row: `change_name="test-change"`, `outcome="success"`, `started_at="2026-01-01T00:00:00"`, `finished_at="2026-01-01T01:00:00"`
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** `result["total"]` equals 1
- **And** `result["by_outcome"]["success"]` equals 1
- **And** `result["avg_duration_seconds"]` is a positive number

---

### Requirement: Proposal detail retrieval

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a `dict` with
keys `proposal_name`, `files`, `phases`, and `phase_state`. If the proposal directory does
not exist, the result SHALL contain an `"error"` key with a descriptive message.

#### Scenario: non-existent proposal returns error

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no directory exists for the proposal name under `base_path/openspec/changes/` or its `archive/` subdirectory
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** the result contains `"proposal_name"` equal to `"nonexistent"`
- **And** the result contains `"error"` with a string mentioning "not found"

#### Scenario: proposal with files and phase state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a change directory exists with `proposal.md`, `clarify.md`, and a `.phase_state` JSON file
- **When** `_build_proposal_detail(db_path, base_path, proposal_name)` is called
- **Then** `result["files"]` contains keys `"proposal.md"` and `"clarify.md"`
- **And** `result["phase_state"]` is a parsed `dict` from the `.phase_state` file

