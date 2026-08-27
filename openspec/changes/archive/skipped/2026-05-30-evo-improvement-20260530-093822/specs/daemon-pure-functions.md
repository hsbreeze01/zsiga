# daemon-pure-functions.md

## ADDED Requirements

### Requirement: _compute_uptime_seconds returns elapsed time or None

`_compute_uptime_seconds(started_at)` SHALL return the number of seconds
elapsed since `started_at` rounded to 1 decimal place. It SHALL return `None`
when the input is falsy, `None`, or an unparseable string.

#### Scenario: valid ISO timestamp returns positive float

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds

- **Given** `started_at` is a valid ISO datetime string in the past (e.g. 60 seconds ago)
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` greater than 0, rounded to 1 decimal place

#### Scenario: None input returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds

- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: empty string input returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds

- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: unparseable string returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds

- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

### Requirement: _build_status_json returns valid JSON with daemon and queue keys

`_build_status_json()` SHALL return a JSON string containing a top-level
`"daemon"` object and a `"queue"` list.

#### Scenario: status JSON structure

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_status_json

- **Given** `_read_daemon_state` returns `{}` and `_scan_proposal_queue` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the result is a valid JSON string with keys `"daemon"` (containing `"state"`, `"pid"`, `"cycle"`) and `"queue"` (an empty list)

### Requirement: _build_metrics_json returns valid JSON

`_build_metrics_json()` SHALL return a JSON string. When the metrics module is
available, it SHALL contain `"summary"` and `"phases"` keys. When the metrics
module raises, it SHALL return `{"error": "<message>"}`.

#### Scenario: metrics JSON with mock compute_stats

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_build_metrics_json

- **Given** `compute_stats()` returns `{"summary": {"total": 5}, "phases": {}}`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON with keys `"summary"` and `"phases"`

