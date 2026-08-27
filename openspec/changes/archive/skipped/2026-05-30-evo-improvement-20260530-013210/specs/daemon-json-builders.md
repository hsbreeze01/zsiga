# daemon-json-builders

Delta spec for JSON builder functions in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: _build_status_json returns daemon status payload

The system SHALL provide `_build_status_json()` that returns a JSON string
containing a top-level `daemon` object with keys `pid`, `state`, `cycle`,
`current_change`, `current_phase`, `current_project`, `heartbeat`,
`uptime_seconds`, and a top-level `queue` array.

#### Scenario: _build_status_json returns valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"pid": 42, "state": "running", "cycle": 5}`
- **And** `_scan_proposal_queue` returns an empty list
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON with keys `daemon` and `queue`
- **And** `daemon["pid"]` is `42`
- **And** `daemon["state"]` is `"running"`

### Requirement: _build_metrics_json returns metrics payload

The system SHALL provide `_build_metrics_json()` that returns a JSON
string with `summary`, `phases`, and `rolling_rates` keys. On error it
MUST return `{"error": "<message>"}`.

#### Scenario: _build_metrics_json returns valid JSON with summary key

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` is mocked to return `{"summary": {"total": 10}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON with key `summary`

#### Scenario: _build_metrics_json returns error on exception

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` raises `RuntimeError("db missing")`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON with key `error`

### Requirement: _build_current_json returns current status payload

The system SHALL provide `_build_current_json()` that returns a JSON
string with `daemon`, `current`, and `queue` keys. The `current` object
MUST include a `phase_progress` array with entries for all pipeline
phases.

#### Scenario: _build_current_json returns JSON with daemon, current, queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state` returns `{"pid": 1, "current_change": "test-change", "current_phase": "IMPLEMENT"}`
- **And** `_scan_proposal_queue` returns `[]`
- **When** `_build_current_json()` is called
- **Then** the result parses as JSON with keys `daemon`, `current`, `queue`
- **And** `current["phase_progress"]` has length 6
