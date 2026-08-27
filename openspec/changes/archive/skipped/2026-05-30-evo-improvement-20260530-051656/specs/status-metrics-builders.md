# status-metrics-builders

## ADDED Requirements

### Requirement: _build_status_json SHALL produce valid JSON with daemon and queue keys

`_build_status_json()` SHALL return a JSON string containing a top-level
`daemon` object (with keys `pid`, `state`, `cycle`, `uptime_seconds`,
`heartbeat`, `current_change`, `current_phase`, `current_project`) and
a top-level `queue` array.

#### Scenario: _build_status_json returns valid JSON with daemon and queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"pid": 42, "state": "running", "cycle": 5,
  "started_at": "2025-01-01T00:00:00", "last_heartbeat": "2025-01-01T08:00:00"}`
  and `_scan_proposal_queue` returns `[]` (both mocked)
- **When** `_build_status_json()` is called
- **Then** the result SHALL be a valid JSON string, and when parsed,
  `result["daemon"]["pid"]` SHALL equal `42`,
  `result["daemon"]["state"]` SHALL equal `"running"`, and
  `result["queue"]` SHALL be a list

#### Scenario: _build_status_json uses safe defaults when daemon state is empty

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{}` and `_scan_proposal_queue` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the parsed result's `daemon.state` SHALL equal `"unknown"`,
  `daemon.pid` SHALL be `None`, and `daemon.uptime_seconds` SHALL be `None`

### Requirement: _build_metrics_json SHALL produce valid JSON

`_build_metrics_json()` SHALL return a JSON string. On success it
contains `summary` and `phases` keys. On failure it contains an `error`
key.

#### Scenario: _build_metrics_json returns error JSON on import failure

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` import raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the result SHALL be valid JSON with an `"error"` key
