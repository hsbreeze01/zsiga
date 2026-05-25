# proposal-stats-endpoint.md

## ADDED Requirements

### Requirement: Proposal Stats Data Query

The system SHALL provide a function `_build_proposal_stats_json` that queries the `changes` table in the local SQLite database and returns a dict with aggregate statistics.

The function MUST accept a `db_path` parameter (string or Path) pointing to the SQLite database file.

The returned dict SHALL contain exactly four top-level keys:
- `total` — integer, total row count in the `changes` table
- `by_outcome` — dict mapping each distinct `outcome` value to its count
- `avg_duration_seconds` — float or `None`, the average duration in seconds between `started_at` and `finished_at` for rows where `finished_at` is not empty; `None` when no rows have a valid duration
- `recent` — list of at most 5 dicts, each with keys `change_name`, `outcome`, `started_at`, `finished_at`, ordered by `id` descending

The function MUST use only read-only SQL queries. It SHALL NOT write to or modify the `changes` table.

The function MUST handle the following error conditions gracefully by returning a dict containing an `"error"` key with a descriptive message:
- The database file does not exist
- The `changes` table does not exist in the database
- Any SQL or connection error occurs

#### Scenario: Query returns correct aggregates from populated table

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table containing 3 rows: two with `outcome='success'` and `finished_at` set, one with `outcome='fail'` and empty `finished_at`
- **When** `_build_proposal_stats_json` is called with the path to this database
- **Then** the returned dict contains `total == 3`, `by_outcome == {"success": 2, "fail": 1}`, `avg_duration_seconds` is a float greater than 0, and `recent` is a list of length 3

#### Scenario: Query returns empty stats from empty table

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table that contains zero rows
- **When** `_build_proposal_stats_json` is called with the path to this database
- **Then** the returned dict contains `total == 0`, `by_outcome == {}`, `avg_duration_seconds is None`, and `recent == []`

#### Scenario: Recent list limited to 5 entries

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table containing 8 rows with distinct IDs
- **When** `_build_proposal_stats_json` is called with the path to this database
- **Then** the `recent` list contains exactly 5 entries, ordered by `id` descending (highest first)

#### Scenario: Recent entries contain required fields

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table containing at least one row with all fields populated
- **When** `_build_proposal_stats_json` is called with the path to this database
- **Then** each item in `recent` contains the keys `change_name`, `outcome`, `started_at`, `finished_at`

#### Scenario: Graceful degradation when database file does not exist

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a file path that does not exist on disk
- **When** `_build_proposal_stats_json` is called with this path
- **Then** the returned dict contains an `"error"` key with a non-empty string value

#### Scenario: Graceful degradation when changes table does not exist

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database that exists but has no `changes` table
- **When** `_build_proposal_stats_json` is called with the path to this database
- **Then** the returned dict contains an `"error"` key with a non-empty string value

#### Scenario: Avg duration ignores rows with empty finished_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database with a `changes` table containing 2 rows: one with both `started_at` and `finished_at` set, one with `finished_at` as empty string
- **When** `_build_proposal_stats_json` is called with the path to this database
- **Then** `avg_duration_seconds` is computed from only the row with a valid `finished_at`, not `None`

---

### Requirement: Proposal Stats HTTP Endpoint

The system SHALL expose an HTTP endpoint `GET /api/proposal-stats` on the dashboard server that returns proposal aggregate statistics as JSON.

The endpoint MUST return HTTP 200 with `Content-Type: application/json` when the query succeeds.

The endpoint MUST return HTTP 500 with `Content-Type: application/json` and a body containing an `"error"` key when the query fails (e.g., database unavailable, table missing).

The response body on success SHALL be the JSON serialization of the dict returned by `_build_proposal_stats_json`.

The endpoint SHALL NOT affect the behavior of existing endpoints (`/api/status.json`, `/api/metrics.json`, `/api/current.json`, `/`).

#### Scenario: GET /api/proposal-stats returns 200 with valid JSON structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a running daemon dashboard server with a valid SQLite database containing at least one change record
- **When** an HTTP GET request is made to `/api/proposal-stats`
- **Then** the response status is 200, Content-Type is `application/json`, and the body parses to a dict with keys `total`, `by_outcome`, `avg_duration_seconds`, `recent`

#### Scenario: Existing endpoint /api/status.json still returns 200

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon module with the new endpoint route added
- **When** `_build_status_json()` is called
- **Then** it returns valid JSON containing `daemon` and `queue` keys, unchanged from before
