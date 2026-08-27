# daemon-status-builders

Delta spec for daemon status and metrics builder functions: `_compute_uptime_seconds`, `_build_status_json`, `_build_metrics_json`.

## ADDED Requirements

### Requirement: compute-uptime-seconds

`_compute_uptime_seconds(started_at)` SHALL return the elapsed time in seconds (rounded to 1 decimal) since the ISO-formatted `started_at` timestamp. It SHALL return `None` when `started_at` is `None`, empty, or unparseable.

#### Scenario: uptime-valid-timestamp

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp from 60 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the returned value is approximately `60.0` (within ±2.0 seconds tolerance)

#### Scenario: uptime-none-input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the returned value is `None`

#### Scenario: uptime-empty-string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the returned value is `None`

#### Scenario: uptime-invalid-string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-datetime"`
- **When** `_compute_uptime_seconds("not-a-datetime")` is called
- **Then** the returned value is `None`

### Requirement: build-status-json

`_build_status_json()` SHALL return a JSON string containing a top-level `"daemon"` object with keys `pid`, `state`, `cycle`, `current_change`, `current_phase`, `current_project`, `heartbeat`, `uptime_seconds` and a top-level `"queue"` list. Values for missing daemon state fields SHALL default to `None` or `"unknown"` for `state`.

#### Scenario: status-json-structure-with-daemon-state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{"pid": 42, "state": "running", "cycle": 3}` and `_scan_proposal_queue()` returns an empty list
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON with `daemon.pid == 42`, `daemon.state == "running"`, `daemon.cycle == 3`, and `queue` is a list

#### Scenario: status-json-defaults-without-daemon-state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state()` returns `{}` and `_scan_proposal_queue()` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON with `daemon.state == "unknown"` and `daemon.pid` is `None`

### Requirement: build-metrics-json

`_build_metrics_json()` SHALL return a JSON string. When `compute_stats()` succeeds, the result SHALL contain `summary`, `phases`, and `rolling_rates` keys. When an exception occurs, the result SHALL contain an `error` key with the exception message.

#### Scenario: metrics-json-success

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` returns `{"summary": {"total": 5}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the parsed JSON contains `summary.total == 5`, a `phases` key, and `rolling_rates` as a list

#### Scenario: metrics-json-error-fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` raises `RuntimeError("db unavailable")`
- **When** `_build_metrics_json()` is called
- **Then** the parsed JSON contains an `error` key with value `"db unavailable"`

