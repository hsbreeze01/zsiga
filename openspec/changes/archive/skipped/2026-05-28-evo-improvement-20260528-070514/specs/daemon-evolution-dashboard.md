# daemon-evolution-dashboard

## ADDED Requirements

### Requirement: health-check-probe
`_health_check(db_path)` SHALL return `{"status": "healthy", "db_records": <int>}`
when the database is accessible and contains a `changes` table.  When the
database file is missing or an error occurs, it SHALL return
`{"status": "unhealthy", "error": "<message>"}`.

#### Scenario: health-check-healthy

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a valid SQLite database with a `changes` table containing 3 rows
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "healthy", "db_records": 3}`

#### Scenario: health-check-unhealthy-missing-db

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a non-existent database path
- **When** `_health_check(db_path)` is called
- **Then** the result has `"status" == "unhealthy"` and contains an `"error"` key

---

### Requirement: proposal-stats-missing-db
`_build_proposal_stats_json(db_path)` SHALL return a dict with an `"error"` key
when the database file does not exist.

#### Scenario: proposal-stats-missing-db

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains an `"error"` key

---

### Requirement: proposal-stats-valid-db
`_build_proposal_stats_json(db_path)` SHALL return aggregate statistics from
the `changes` table including `total`, `by_outcome`, `avg_duration_seconds`,
and `recent` keys when the database exists and is valid.

#### Scenario: proposal-stats-valid-db

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a valid SQLite database with a `changes` table containing rows
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains `total`, `by_outcome`, `avg_duration_seconds`, and `recent` keys
