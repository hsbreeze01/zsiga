# daemon-status-builders

Delta spec for `zsiga/daemon.py` status and metrics JSON builder functions.

## ADDED Requirements

### Requirement: Uptime Computation

`_compute_uptime_seconds(started_at)` SHALL compute the elapsed time in seconds
since the given ISO timestamp, rounded to 1 decimal place. It MUST return `None`
when the input is missing, empty, or cannot be parsed.

#### Scenario: compute uptime with valid ISO timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp from 60 seconds ago
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result SHALL be a float approximately equal to 60.0 (±2.0)

#### Scenario: compute uptime with None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result SHALL be `None`

#### Scenario: compute uptime with empty string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result SHALL be `None`

#### Scenario: compute uptime with invalid string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result SHALL be `None`

### Requirement: Status JSON Builder

`_build_status_json()` SHALL return a valid JSON string containing a `daemon`
object with state, uptime, and cycle info, and a `queue` array from proposal
scanning.

#### Scenario: build status json with empty daemon state

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `daemon_state.json` does not exist and the proposal queue is empty
- **When** `_build_status_json()` is called
- **Then** the result SHALL be valid JSON
- **And** `parsed["daemon"]["state"]` SHALL be `"unknown"` (the default)
- **And** `parsed["queue"]` SHALL be an empty list

#### Scenario: build status json with populated daemon state

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `daemon_state.json` contains `{"state": "running", "cycle": 5, "started_at": "<recent ISO>"}`
- **When** `_build_status_json()` is called
- **Then** `parsed["daemon"]["state"]` SHALL be `"running"`
- **And** `parsed["daemon"]["cycle"]` SHALL be `5`
- **And** `parsed["daemon"]["uptime_seconds"]` SHALL be a non-negative number

### Requirement: Metrics JSON Builder

`_build_metrics_json()` SHALL return a valid JSON string. On success it SHALL
contain `summary`, `phases`, and `rolling_rates` keys. On failure it SHALL
contain an `error` key.

#### Scenario: build metrics json with compute_stats failure

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats()` raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the result SHALL be valid JSON containing an `"error"` key
