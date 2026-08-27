# daemon-queue-scanning

Delta spec for `_scan_proposal_queue` in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: _scan_proposal_queue scans change directories for proposals

The system SHALL provide `_scan_proposal_queue(changes_dir)` that walks
the given directory, filters for subdirectories containing `proposal.md`,
and returns a list of dicts. Each dict MUST contain keys `name`,
`project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`,
`consecutive_fails`.

#### Scenario: _scan_proposal_queue returns empty list for missing directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a non-existent path
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: _scan_proposal_queue returns empty list for empty directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is an empty directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: _scan_proposal_queue finds proposals with proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `my-change/` with a `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result has length 1
- **And** the first entry's `name` is `"my-change"`

#### Scenario: _scan_proposal_queue skips directories without proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `empty-dir/` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: _scan_proposal_queue extracts summary from first heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `proposal.md` first line starting with `# ` is `# My Cool Proposal`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the first entry's `summary` is `"My Cool Proposal"`

#### Scenario: _scan_proposal_queue detects CLARIFY phase when only proposal.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory has only `proposal.md` (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the first entry's `phase` is `"CLARIFY"`

#### Scenario: _scan_proposal_queue detects ENRICH phase when clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory has `proposal.md` and `clarify.md` (no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the first entry's `phase` is `"ENRICH"`

#### Scenario: _scan_proposal_queue detects IMPLEMENT phase when specs dir has md files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory has `proposal.md`, `clarify.md`, and `specs/some-spec.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the first entry's `phase` is `"IMPLEMENT"`

#### Scenario: _scan_proposal_queue detects manual paused state from .paused file

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory contains a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `paused` is `True`
- **And** the entry's `lifecycle` is `"paused"`
