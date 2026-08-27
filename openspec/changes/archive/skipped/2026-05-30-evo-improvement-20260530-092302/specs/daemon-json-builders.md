# daemon-json-builders.md — JSON Builders and Dashboard Handlers

## ADDED Requirements

### Requirement: compute_uptime_seconds_returns_elapsed
`_compute_uptime_seconds(started_at)` SHALL return the elapsed time in seconds since `started_at` rounded to 1 decimal, or `None` if the input is missing or unparseable.

#### Scenario: uptime_with_valid_iso_string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** a valid ISO-format datetime string representing a time in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a positive float rounded to 1 decimal place

#### Scenario: uptime_with_none

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** it returns `None`

#### Scenario: uptime_with_invalid_string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** an unparseable string like `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** it returns `None`

---

### Requirement: build_status_json_produces_valid_payload
`_build_status_json()` SHALL return a JSON string containing a top-level `daemon` object with key `state` and a top-level `queue` list.

#### Scenario: status_json_structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** daemon state is empty (no state file) and no proposals exist
- **When** `_build_status_json()` is called
- **Then** the result is valid JSON with a `daemon` key (containing `state` and `queue` key containing a list)

---

### Requirement: build_current_json_produces_valid_payload
`_build_current_json()` SHALL return a JSON string containing top-level `daemon`, `current`, and `queue` keys.

#### Scenario: current_json_structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** daemon state is empty (no state file) and no proposals exist
- **When** `_build_current_json()` is called
- **Then** the result is valid JSON with `daemon`, `current`, and `queue` keys; `current` contains a `phase_progress` list

---

### Requirement: health_check_probes_database
`_health_check(db_path)` SHALL return `{"status": "healthy", "db_records": <int>}` on success or `{"status": "unhealthy", "error": "<msg>"}` on failure.

#### Scenario: health_check_with_valid_db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** it returns `{"status": "healthy", "db_records": 3}`

#### Scenario: health_check_with_missing_db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a path that does not exist
- **When** `_health_check("/nonexistent/path.db")` is called
- **Then** it returns a dict with `"status"` equal to `"unhealthy"`

---

### Requirement: build_pipeline_status_structure
`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys `active_proposal`, `current_phase`, `phase_progress`, `queue`, and `daemon`.

#### Scenario: pipeline_status_empty_state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** no daemon state file, no changes directory, and no database
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result dict has `active_proposal` as `None`, `phase_progress` as an empty list, and `queue` as an empty list

---

### Requirement: build_proposal_detail_returns_structure
`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict with `proposal_name`, `files`, `phases`, and `phase_state` keys. If the proposal directory does not exist, it SHALL include an `error` key.

#### Scenario: proposal_detail_not_found

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** no matching proposal directory anywhere under changes or archive
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent-proposal")` is called
- **Then** the result dict contains `error` key and `proposal_name` equal to `"nonexistent-proposal"`

#### Scenario: proposal_detail_found_with_files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory containing `proposal.md` with content `# Test Proposal`
- **When** `_build_proposal_detail(db_path, base_path, "test-proposal")` is called
- **Then** the result dict has `files` containing `"proposal.md"` key with the file content, and `proposal_name` is `"test-proposal"`

---

### Requirement: build_proposal_stats_returns_aggregates
`_build_proposal_stats_json(db_path)` SHALL return a dict with `total`, `by_outcome`, `avg_duration_seconds`, and `recent` keys on success, or `{"error": "<msg>"}` on failure.

#### Scenario: proposal_stats_missing_db

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a non-existent database path
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains an `"error"` key with a message about the missing file
