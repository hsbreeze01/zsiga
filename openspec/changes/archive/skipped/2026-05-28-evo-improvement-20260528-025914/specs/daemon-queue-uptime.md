# daemon-queue-uptime — Queue Scanning & Uptime Computation

## ADDED Requirements

### Requirement: Proposal queue scanning

`_scan_proposal_queue(changes_dir)` SHALL walk the given `changes_dir` and return a list of
`dict` entries, one per subdirectory that contains a `proposal.md` file. Each entry SHALL
contain at minimum the keys `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`,
`paused_reason`, and `consecutive_fails`. Non-directory entries and directories without
`proposal.md` SHALL be skipped.

#### Scenario: empty directory returns empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is an empty directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list `[]`

#### Scenario: directory without proposal.md is skipped

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `no-proposal` without a `proposal.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list

#### Scenario: single proposal extracted correctly

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `my-change` with a `proposal.md` whose first `#`-heading line reads `# Add Feature X`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is a list of length 1
- **And** `result[0]["name"]` equals `"my-change"`
- **And** `result[0]["summary"]` equals `"Add Feature X"`

#### Scenario: summary fallback when no heading found

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `bare-change` with a `proposal.md` that has no `#` heading line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** `result[0]["summary"]` equals `"—"` (em dash fallback)

#### Scenario: phase detection from output files

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `with-specs` with `proposal.md` and a `specs/` directory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** `result[0]["phase"]` equals `"IMPLEMENT"`

---

### Requirement: Uptime computation

`_compute_uptime_seconds(started_at)` SHALL compute elapsed seconds from the given ISO
8601 timestamp to now, rounded to 1 decimal. It SHALL return `None` when the input is
`None`, empty string, or unparseable.

#### Scenario: None input returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is `None`

#### Scenario: empty string returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is `None`

#### Scenario: valid recent timestamp returns non-negative float

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is the ISO 8601 string for the current time
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` greater than or equal to 0
- **And** the result is rounded to 1 decimal place

#### Scenario: invalid string returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is `None`

