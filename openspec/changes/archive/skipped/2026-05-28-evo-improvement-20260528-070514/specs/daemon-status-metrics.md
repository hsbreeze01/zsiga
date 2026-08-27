# daemon-status-metrics

## ADDED Requirements

### Requirement: compute-uptime-seconds
`_compute_uptime_seconds(started_at)` SHALL compute the elapsed seconds since
the ISO-format `started_at` timestamp, rounded to one decimal place.  It MUST
return `None` when `started_at` is `None`, empty string, or an unparseable
value.

#### Scenario: none-started-at-returns-none

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: empty-string-returns-none

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: invalid-iso-returns-none

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

#### Scenario: valid-iso-returns-positive-float

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp 60 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` greater than `59.0`

---

### Requirement: build-status-json-structure
`_build_status_json()` SHALL return a JSON string containing a top-level
`"daemon"` object and a `"queue"` array.  The `"daemon"` object MUST include
the keys `pid`, `state`, `cycle`, `uptime_seconds`, `heartbeat`,
`current_change`, `current_phase`, and `current_project`.

#### Scenario: status-json-has-daemon-and-queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** daemon state is empty (no state file) and proposal queue is empty
- **When** `_build_status_json()` is called
- **Then** the parsed result contains a `"daemon"` dict and a `"queue"` list

#### Scenario: daemon-object-has-required-keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** daemon state contains `{"pid": 42, "state": "running", "cycle": 5}`
- **When** `_build_status_json()` is called
- **Then** the `daemon` object contains keys `pid`, `state`, `cycle`, `uptime_seconds`, `heartbeat`, `current_change`, `current_phase`, `current_project`

---

### Requirement: build-metrics-json-structure
`_build_metrics_json()` SHALL return a JSON string.  When `compute_stats()`
succeeds, the result MUST contain `"summary"` and `"phases"` keys.  When an
exception occurs, it SHALL return a JSON string with an `"error"` key.

#### Scenario: metrics-json-success-structure

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` returns `{"summary": {"total": 10}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the parsed result contains `"summary"` and `"phases"` keys

#### Scenario: metrics-json-error-fallback

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the parsed result contains an `"error"` key
