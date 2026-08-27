# daemon-status-builders

## ADDED Requirements

### Requirement: Compute uptime from started_at timestamp

`_compute_uptime_seconds(started_at)` SHALL return the elapsed time in
seconds (rounded to 1 decimal place) between the given ISO-format
`started_at` and the current wall clock. When `started_at` is `None` or
an empty string or unparseable, it SHALL return `None`.

#### Scenario: Returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: Returns None for empty string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: Returns None for invalid ISO string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

#### Scenario: Returns positive elapsed for valid past timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO datetime string in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a positive `float` rounded to 1 decimal place

---

### Requirement: Build status JSON payload

`_build_status_json()` SHALL return a JSON string containing a top-level
`"daemon"` object and a `"queue"` array. The `"daemon"` object SHALL
include `uptime_seconds` derived from the stored `started_at`.

#### Scenario: Returns valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"state": "running", "started_at": "2025-01-01T00:00:00"}`
  and `_scan_proposal_queue` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON and has keys `"daemon"` and `"queue"`

#### Scenario: Daemon object includes uptime_seconds

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` returns `{"state": "running", "started_at": "2025-01-01T00:00:00"}`
  and `_scan_proposal_queue` returns `[]`
- **When** `_build_status_json()` is called
- **Then** the parsed result's `"daemon"` object has key `"uptime_seconds"`
  with a numeric value

---

### Requirement: Build metrics JSON payload

`_build_metrics_json()` SHALL return a JSON string. On success it SHALL
contain `"summary"` and `"phases"` keys. On failure it SHALL contain an
`"error"` key.

#### Scenario: Returns error JSON when compute_stats raises

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` from `zsiga.metrics.dashboard` raises `ImportError`
- **When** `_build_metrics_json()` is called
- **Then** the result parses as JSON and has key `"error"`

---

### Requirement: Build pipeline status from DB and filesystem

`_build_pipeline_status(db_path, base_path)` SHALL return a dict with
keys `active_proposal`, `current_phase`, `phase_progress`, `queue`,
`daemon`. When no daemon state exists, `active_proposal` SHALL be `None`.

#### Scenario: Returns structure with all required keys when empty

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{}`, `db_path` points to a
  non-existent file, and `base_path` has no `openspec/changes/` directory
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result dict has keys `active_proposal`, `current_phase`,
  `phase_progress`, `queue`, `daemon` and `active_proposal` is `None`

#### Scenario: Daemon sub-dict contains state and cycle

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"state": "running", "cycle": 7}`
  and no changes dir and no DB
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result's `daemon` dict has `"state"` equal to `"running"`
  and `"cycle"` equal to `7`

#### Scenario: Queue includes proposals from changes directory

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `base_path` has `openspec/changes/test-proposal/proposal.md`
  and daemon state has no `current_change`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result's `queue` list contains an entry with
  `"name"` equal to `"test-proposal"`

#### Scenario: Active proposal detected from daemon state

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"current_change": "my-change"}`
  and `base_path` has `openspec/changes/my-change/proposal.md`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result's `active_proposal` equals `"my-change"`
