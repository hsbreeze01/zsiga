# Delta Spec: JSON Builder Functions

## ADDED Requirements

### Requirement: build-status-json

The system SHALL provide `_build_status_json()` that returns a JSON string
containing a top-level `daemon` object (with `pid`, `state`, `cycle`,
`current_change`, `current_phase`, `current_project`, `heartbeat`,
`uptime_seconds` keys) and a top-level `queue` array.

#### Scenario: returns-valid-json-with-daemon-and-queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{"pid": 1, "state": "running", "cycle": 3, "started_at": "2026-01-01T00:00:00"}`
- **And** `_scan_proposal_queue()` returns an empty list
- **When** `_build_status_json()` is called
- **Then** the result is a valid JSON string
- **And** parsing the result yields a dict with keys `daemon` and `queue`

#### Scenario: daemon-object-has-required-fields

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{"pid": 1, "state": "running", "cycle": 3, "started_at": "2026-01-01T00:00:00"}`
- **And** `_scan_proposal_queue()` returns `[]`
- **When** `_build_status_json()` is called and the result is parsed
- **Then** `daemon` dict contains keys `pid`, `state`, `cycle`, `uptime_seconds`, `heartbeat`

### Requirement: build-metrics-json

The system SHALL provide `_build_metrics_json()` that returns a JSON string.
When the metrics subsystem is unavailable it SHALL return a JSON object with
an `error` key.

#### Scenario: returns-valid-json-on-error

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** the `metrics.dashboard` module is unavailable (import fails)
- **When** `_build_metrics_json()` is called
- **Then** the result is a valid JSON string
- **And** parsing the result yields a dict containing an `error` key
