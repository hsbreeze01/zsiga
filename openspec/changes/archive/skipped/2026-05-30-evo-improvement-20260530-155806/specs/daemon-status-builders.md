# daemon-status-builders

## ADDED Requirements

### Requirement: _compute_uptime_seconds handles edge cases

`_compute_uptime_seconds()` SHALL return `None` for missing or unparseable
timestamps and a positive rounded float for valid ISO timestamps.

#### Scenario: Returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: Returns None for empty string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: Returns None for invalid timestamp string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-timestamp"`
- **When** `_compute_uptime_seconds("not-a-timestamp")` is called
- **Then** the result is `None`

#### Scenario: Returns positive float for valid recent timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp from 5 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` >= 4.0 and the result is rounded to 1 decimal place

### Requirement: _build_status_json produces valid JSON with daemon and queue

`_build_status_json()` SHALL return a JSON string containing a top-level
`daemon` object and a `queue` array.

#### Scenario: Output is valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{"state": "running", "cycle": 1}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the result is a valid JSON string with keys `"daemon"` and `"queue"`

#### Scenario: Daemon object contains uptime_seconds

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{"started_at": "2025-01-01T00:00:00"}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_status_json()` is called and the result is parsed as JSON
- **Then** `result["daemon"]["uptime_seconds"]` is a number or `None`

### Requirement: _build_metrics_json handles errors gracefully

When the metrics computation fails, `_build_metrics_json()` SHALL return a
JSON string containing an `error` key.

#### Scenario: Returns error JSON when compute_stats raises

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `zsiga.metrics.dashboard.compute_stats` raises `RuntimeError("db unavailable")`
- **When** `_build_metrics_json()` is called
- **Then** the result is a valid JSON string containing key `"error"` with value `"db unavailable"`
