# uptime-seconds-field

## ADDED Requirements

### Requirement: daemon status SHALL include uptime_seconds

The `_build_status_json` function in `zsiga/daemon.py` SHALL compute and include an
`uptime_seconds` field in the `daemon` object returned by `/api/status.json`.

The value SHALL be derived from the existing `started_at` ISO timestamp stored in
`daemon_state.json`. The calculation SHALL use `datetime.fromisoformat()` to parse
the timestamp, compute elapsed seconds via `datetime.now()` difference, and round
to one decimal place.

When `started_at` is absent, empty, or cannot be parsed as an ISO datetime,
`uptime_seconds` SHALL be `null` (JSON `null` / Python `None`).

When `started_at` contains timezone information, the computation SHALL convert
both timestamps to UTC for comparison to avoid local-time ambiguity.

No new module-level variables or imports SHALL be introduced beyond `datetime`
(which is already imported in `daemon.py`).

#### Scenario: uptime_seconds present with valid started_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `daemon_state.json` contains a valid `started_at` ISO timestamp (e.g. `"2025-06-01T12:00:00"`)
- **When** `_build_status_json()` is called
- **Then** the returned JSON `daemon` object SHALL contain `"uptime_seconds"` with a positive numeric value rounded to 1 decimal place

#### Scenario: uptime_seconds null when started_at is missing

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `daemon_state.json` does not contain a `started_at` key, or the file does not exist
- **When** `_build_status_json()` is called
- **Then** the returned JSON `daemon` object SHALL contain `"uptime_seconds": null`

#### Scenario: uptime_seconds null when started_at is unparseable

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `daemon_state.json` contains a `started_at` value that is not a valid ISO datetime (e.g. `""`, `"garbage"`, `"not-a-date"`)
- **When** `_build_status_json()` is called
- **Then** the returned JSON `daemon` object SHALL contain `"uptime_seconds": null` and SHALL NOT raise an exception

#### Scenario: uptime_seconds monotonically increasing

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `daemon_state.json` contains a valid `started_at` in the recent past
- **When** `_build_status_json()` is called twice with a short time interval between calls
- **Then** the second `uptime_seconds` value SHALL be strictly greater than the first

#### Scenario: existing daemon fields remain unchanged

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `daemon_state.json` contains all standard fields (`pid`, `state`, `cycle`, `current_change`, `current_phase`, `current_project`, `last_heartbeat`)
- **When** `_build_status_json()` is called
- **Then** all pre-existing fields in the `daemon` object SHALL retain their original values, and `uptime_seconds` SHALL be present as an additional field

#### Scenario: timezone-aware started_at handled correctly

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `daemon_state.json` contains a `started_at` value with timezone information (e.g. `"2025-06-15T10:00:00+08:00"`)
- **When** `_build_status_json()` is called
- **Then** the returned `uptime_seconds` SHALL be a positive numeric value representing the correct elapsed seconds (accounting for timezone conversion)
- **And** a timezone-aware and a timezone-naive `started_at` referring to approximately the same moment SHALL produce `uptime_seconds` values within 5 seconds of each other
