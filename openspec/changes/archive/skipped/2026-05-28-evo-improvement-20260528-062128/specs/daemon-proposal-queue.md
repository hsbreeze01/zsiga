# daemon-proposal-queue

## ADDED Requirements

### REQ-PQ-01: Proposal queue scanning

`_scan_proposal_queue` SHALL walk a changes directory and return a list of proposal
entries. Each entry MUST contain keys: `name`, `project`, `summary`, `phase`,
`lifecycle`, `paused`, `paused_reason`, `consecutive_fails`.

It SHALL skip non-directory entries, directories without `proposal.md`, and
SHALL gracefully handle unreadable `proposal.md` files.

When `changes_dir` is `None`, it SHALL resolve the path from `ZSIGA_HOME`.

#### Scenario: scan-empty-directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory that exists but is empty
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** returns `[]`

#### Scenario: scan-finds-proposals

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory with two subdirectories each containing a
  `proposal.md` with a `# ` heading line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** returns a list of two dicts, each containing keys `name`, `project`,
  `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`

#### Scenario: scan-skips-files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a plain file named `README.md`
  alongside valid proposal subdirectories
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the file entry is skipped and only subdirectory entries appear in the result

#### Scenario: scan-skips-dir-without-proposal-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory with a subdirectory that has no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** that subdirectory is not included in the result

#### Scenario: scan-extracts-summary-from-heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `proposal.md` whose first `# ` line reads `# Fix logging bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the corresponding entry's `summary` is `"Fix logging bug"`

#### Scenario: scan-detects-clarify-phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory with only `proposal.md` (no `clarify.md`,
  no `specs/` directory)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"CLARIFY"`

#### Scenario: scan-detects-enrich-phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory with `proposal.md` and `clarify.md` but no
  `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"ENRICH"`

#### Scenario: scan-detects-implement-phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory with `proposal.md`, `clarify.md`, and a
  `specs/` directory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"IMPLEMENT"`

#### Scenario: scan-nonexistent-directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a path that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** returns `[]`

### REQ-PQ-02: Uptime computation

`_compute_uptime_seconds` SHALL compute elapsed seconds since the given ISO
timestamp, rounded to 1 decimal place. It SHALL return `None` when the input
is `None`, empty string, or cannot be parsed.

#### Scenario: uptime-valid-timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** a valid ISO timestamp 100 seconds in the past (via monkeypatching
  `datetime.now`)
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** returns a float approximately equal to `100.0`

#### Scenario: uptime-none-input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** returns `None`

#### Scenario: uptime-empty-string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is an empty string `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** returns `None`

#### Scenario: uptime-invalid-string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** returns `None`
