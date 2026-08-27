# daemon-proposal-scanning

Delta spec for testing the proposal queue scanner in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: Proposal queue scanning

`_scan_proposal_queue(changes_dir)` SHALL walk the given directory and
return a list of proposal dicts. Each entry SHALL include keys
`name`, `project`, `summary`, `phase`, `lifecycle`, `paused`,
`paused_reason`, and `consecutive_fails`.

#### Scenario: Nonexistent changes directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is a path that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: Directory with one valid proposal

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing one subdirectory `fix-logging` with a `proposal.md` whose first heading line is `# Fix Logging Bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result has length 1
- **And** the entry has `name` equal to `"fix-logging"`
- **And** the entry has `summary` equal to `"Fix Logging Bug"`

#### Scenario: Subdirectory without proposal.md is skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing one subdirectory `empty-dir` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: Phase detection from output files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `clarify.md` but no `specs/` subdirectory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase` equal to `"ENRICH"`

#### Scenario: Proposal with specs directory reaches IMPLEMENT phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has both `clarify.md` and a `specs/` subdirectory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase` equal to `"IMPLEMENT"`

#### Scenario: Manual .paused file marks proposal paused

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory containing a `.paused` file and a `proposal.md`
- **And** the metrics DB lookup is mocked to raise (no DB)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused` equal to `True`
- **And** the entry has `paused_reason` equal to `"manual"`
