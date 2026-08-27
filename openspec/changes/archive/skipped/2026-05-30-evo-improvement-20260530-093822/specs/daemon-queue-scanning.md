# daemon-queue-scanning

## ADDED Requirements

### Requirement: _scan_proposal_queue SHALL enumerate proposals from changes directory

`_scan_proposal_queue(changes_dir)` SHALL walk the given directory,
identify subdirectories containing `proposal.md`, and return a list of
 dicts with keys `name`, `project`, `summary`, `phase`, `lifecycle`,
 `paused`, `paused_reason`, `consecutive_fails`.

#### Scenario: empty changes directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` that exists but contains no subdirectories with `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it SHALL return `[]`

#### Scenario: non-existent changes directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` `Path` that does not exist on disk
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it SHALL return `[]`

#### Scenario: proposal with proposal.md returns entry with summary

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing a subdirectory `my-change` with `proposal.md` whose first heading line is `# Fix the bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list SHALL contain exactly one entry with `name == "my-change"` and `summary == "Fix the bug"`

#### Scenario: proposal without markdown heading uses dash as summary

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing a subdirectory `no-heading` with `proposal.md` that has no `# ` heading line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry SHALL have `summary == "—"`

#### Scenario: phase detection from clarify.md and specs directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory that contains `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry SHALL have `phase == "ENRICH"`

#### Scenario: phase detection with specs directory advances to IMPLEMENT

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory that contains both `clarify.md` and a `specs/` directory with at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry SHALL have `phase == "IMPLEMENT"`

#### Scenario: proposal without clarify.md has phase CLARIFY

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory that has `proposal.md` but no `clarify.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry SHALL have `phase == "CLARIFY"`

#### Scenario: manual .paused file marks proposal paused

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal subdirectory containing a `.paused` file (and `proposal.md`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry SHALL have `paused == True` and `lifecycle == "paused"` and `paused_reason == "manual"`

#### Scenario: subdirectory without proposal.md is skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing a subdirectory `bare-dir` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list SHALL NOT contain any entry with `name == "bare-dir"`

#### Scenario: non-directory entries are skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing a regular file `notes.txt`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list SHALL be empty (or not contain `notes.txt`)
