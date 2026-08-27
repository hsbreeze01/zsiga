# daemon-status-api-tests

## ADDED Requirements

### Requirement: _build_status_json SHALL return valid JSON with daemon and queue

`_build_status_json()` SHALL return a JSON string with top-level keys
`"daemon"` and `"queue"`. The `"daemon"` object SHALL include `state`, `cycle`,
and `uptime_seconds`.

#### Scenario: build_status_json returns valid JSON structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{"state": "running", "cycle": 7, "started_at": <10 seconds ago>}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON with key `"daemon"` containing `"state": "running"` and `"cycle": 7`
- **And** `"uptime_seconds"` is a positive number

---

### Requirement: _build_metrics_json SHALL return valid JSON or error payload

`_build_metrics_json()` SHALL return a JSON string. When the metrics module
is unavailable or raises, it SHALL return `{"error": "..."}`.

#### Scenario: build_metrics_json handles missing metrics module

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `zsiga.metrics.dashboard.compute_stats` raises `ImportError`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON with key `"error"`

---

### Requirement: _build_current_json SHALL return daemon info with phase progress

`_build_current_json()` SHALL return a JSON string containing daemon info,
current change details, and a `phase_progress` array with exactly 6 entries
(one per pipeline phase).

#### Scenario: build_current_json has six phase progress entries

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state()` returns `{"state": "running", "current_phase": "IMPLEMENT"}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_current_json()` is called
- **Then** the parsed JSON's `current.phase_progress` has length 6
- **And** the entry with `name == "IMPLEMENT"` has `status == "active"`

---

### Requirement: _build_proposal_stats_json SHALL aggregate DB statistics

`_build_proposal_stats_json()` SHALL return a dict with `total`, `by_outcome`,
`avg_duration_seconds`, and `recent` keys on success, or an `error` key on
failure.

#### Scenario: stats_json with missing database file

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a file that does not exist
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result contains key `"error"` with a non-empty string

#### Scenario: stats_json with valid database

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database at `db_path` with a `changes` table containing 2 rows (one `success`, one `fail`)
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** `result["total"]` equals `2`
- **And** `result["by_outcome"]` contains keys `"success"` and `"fail"`
