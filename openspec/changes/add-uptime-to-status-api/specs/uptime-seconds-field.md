# uptime-seconds-field

## ADDED Requirements

### Requirement: uptime_seconds in daemon status response

The `_build_status_json` function SHALL include an `uptime_seconds` field in the `daemon` object of the status JSON payload.

The value SHALL be calculated as the elapsed wall-clock seconds between the current time and the `started_at` ISO timestamp read from daemon state. The result SHALL be rounded to one decimal place.

When `started_at` is absent or cannot be parsed as an ISO timestamp, the value SHALL be `null` (Python `None`, serialized as JSON `null`).

#### Scenario: uptime_seconds present with valid started_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state contains a valid `started_at` ISO timestamp (e.g. `"2025-06-01T12:00:00"`)
- **When** `_build_status_json` is called
- **Then** the parsed response `daemon` object contains `uptime_seconds` as a positive float, rounded to 1 decimal place

#### Scenario: uptime_seconds is null when started_at is missing

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state has no `started_at` key
- **When** `_build_status_json` is called
- **Then** the parsed response `daemon` object contains `uptime_seconds` with value `null`

#### Scenario: uptime_seconds is null when started_at is unparseable

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state contains `started_at` with a value that is not a valid ISO timestamp (e.g. `"garbage"`)
- **When** `_build_status_json` is called
- **Then** the parsed response `daemon` object contains `uptime_seconds` with value `null`

#### Scenario: uptime_seconds increases between consecutive calls

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state contains a valid `started_at` ISO timestamp in the recent past
- **When** `_build_status_json` is called twice with a short delay between calls
- **Then** the second `uptime_seconds` value is strictly greater than the first

#### Scenario: existing daemon fields remain unchanged

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state contains `pid`, `state`, `cycle`, `current_change`, `current_phase`, `current_project`, and `last_heartbeat`
- **When** `_build_status_json` is called
- **Then** the parsed response `daemon` object contains all pre-existing fields (`pid`, `state`, `cycle`, `current_change`, `current_phase`, `current_project`, `heartbeat`) with their expected values, in addition to `uptime_seconds`
