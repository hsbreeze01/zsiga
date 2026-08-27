# daemon-lock-and-scan-tests

## ADDED Requirements

### Requirement: Lock acquisition and release
`acquire_lock()` SHALL obtain an exclusive non-blocking file lock on the PID
lock file. On success it MUST return `(fd, True)` and write the current PID to
the lock file. On failure (another process holds the lock) it MUST return
`(None, False)`. `release_lock(fd)` SHALL close the file descriptor and remove
the lock file.

#### Scenario: acquire_lock succeeds on fresh lock
- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no existing lock file
- **When** `acquire_lock()` is called
- **Then** the returned tuple is `(fd, True)` where `fd` is a file object and the lock file contains the current PID

#### Scenario: release_lock removes lock file
- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and a valid fd is held
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists

#### Scenario: acquire_lock fails when already held
- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another process (or fd) already holds the lock
- **When** `acquire_lock()` is called a second time
- **Then** the returned tuple is `(None, False)`

### Requirement: Proposal queue scanning
`_scan_proposal_queue(changes_dir)` SHALL walk the given changes directory and
return a list of proposal entry dicts sorted by directory name. Each entry MUST
contain keys `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`,
`paused_reason`, `consecutive_fails`.

Directories without `proposal.md` SHALL be skipped. The summary SHALL be
extracted from the first `# ` heading line in `proposal.md`.

Lifecycle detection:
- `completed` — last outcome is `success`
- `paused` — `.paused` file exists, or ≥3 consecutive fails
- `stuck` — last outcome is `fail`/`reverted` but <3 consecutive
- `active` — last outcome exists but is none of the above
- `waiting` — no metrics record found

Phase detection:
- `CLARIFY` — no `clarify.md`
- `ENRICH` — has `clarify.md` but no `specs/*.md`
- `IMPLEMENT` — has `specs/*.md`

#### Scenario: empty changes directory returns empty list
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is an empty directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: directory without proposal.md is skipped
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a subdirectory `no-proposal/` exists but contains no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: valid proposal directory returns entry with summary
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a subdirectory `fix-logging/` contains `proposal.md` with first line `# Fix logging bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result has length 1, the entry's `name` is `"fix-logging"` and `summary` is `"Fix logging bug"`

#### Scenario: phase detection based on output files
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a subdirectory has `proposal.md` and `clarify.md` but no `specs/`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"ENRICH"`

#### Scenario: multiple directories returned sorted
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** subdirectories `beta-change/` and `alpha-change/` both contain `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result has 2 entries ordered `[alpha-change, beta-change]` by name

#### Scenario: paused file sets paused flag
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `paused` is `True` and `lifecycle` is `"paused"`

#### Scenario: non-dir changes_dir returns empty list
- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is None (falls back to non-existent default)
- **When** `_scan_proposal_queue(nonexistent_dir)` is called where `nonexistent_dir` does not exist
- **Then** the result is `[]`
