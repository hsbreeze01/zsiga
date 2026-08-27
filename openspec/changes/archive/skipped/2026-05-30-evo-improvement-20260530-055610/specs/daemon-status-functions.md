# daemon-status-functions

## ADDED Requirements

### Requirement: Uptime computation

`_compute_uptime_seconds(started_at)` SHALL return the elapsed time in seconds
(rounded to one decimal place) since the ISO-format `started_at` timestamp.
It SHALL return `None` when `started_at` is `None`, an empty string, or an
unparseable value.

#### Scenario: Returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: Returns None for empty string input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: Returns None for unparseable string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

#### Scenario: Returns positive elapsed seconds for valid ISO timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp in the recent past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` greater than `0`, rounded to one decimal

### Requirement: Status JSON payload structure

`_build_status_json()` SHALL return a JSON string containing a top-level
`"daemon"` object with at least the keys `"state"`, `"cycle"`, `"pid"`,
`"uptime_seconds"`, and a top-level `"queue"` list.

#### Scenario: Returns valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state and proposal queue can be read (even if empty)
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON and contains both `"daemon"` and `"queue"`
  keys; the `"daemon"` value includes `"state"`, `"cycle"`, `"pid"`, and
  `"uptime_seconds"` keys

### Requirement: Metrics JSON payload structure

`_build_metrics_json()` SHALL return a JSON string.  When the metrics module
is available, it SHALL contain `"summary"` and `"phases"` keys.  When the
metrics module raises an exception, it SHALL return `{"error": "<message>"}`.

#### Scenario: Returns JSON with summary and phases on success

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` returns `{"summary": {"total": 5}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON and contains `"summary"` and `"phases"` keys

#### Scenario: Returns error JSON when compute_stats raises

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` raises `RuntimeError("db down")`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON and contains an `"error"` key with the
  exception message
