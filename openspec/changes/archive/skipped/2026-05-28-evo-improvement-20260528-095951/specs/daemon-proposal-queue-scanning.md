# daemon-proposal-queue-scanning

Delta spec for `zsiga/daemon.py::_scan_proposal_queue`.

## ADDED Requirements

### Requirement: Proposal Queue Discovery

`_scan_proposal_queue(changes_dir)` SHALL walk the changes directory and return
a list of proposal entry dicts, each containing `name`, `project`, `summary`,
`phase`, `lifecycle`, `paused`, `paused_reason`, and `consecutive_fails`.

#### Scenario: scan empty directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** the changes directory exists but contains no subdirectories
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result SHALL be an empty list `[]`

#### Scenario: scan non-existent directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** the changes directory does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called with that path
- **Then** the result SHALL be an empty list `[]`

#### Scenario: scan skips directories without proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** the changes directory contains a subdirectory without `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result SHALL not contain an entry for that subdirectory

#### Scenario: scan extracts summary from proposal.md heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` containing `# My Feature` as its first heading
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the corresponding entry SHALL have `summary` equal to `"My Feature"`

#### Scenario: scan detects CLARIFY phase when only proposal.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory that has `proposal.md` but no `clarify.md` and no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry SHALL have `phase` equal to `"CLARIFY"`

#### Scenario: scan detects ENRICH phase when clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory that has both `proposal.md` and `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry SHALL have `phase` equal to `"ENRICH"`

#### Scenario: scan detects IMPLEMENT phase when specs directory has markdown files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md`, `clarify.md`, and a `specs/` directory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry SHALL have `phase` equal to `"IMPLEMENT"`

#### Scenario: scan marks proposal as paused via .paused file

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory that contains a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry SHALL have `paused` equal to `True`
- **And** `paused_reason` SHALL be `"manual"`
- **And** `lifecycle` SHALL be `"paused"`

#### Scenario: scan detects consecutive failures from metrics

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory and `load_all_changes()` returns records where the last 3 entries for this change have outcome `fail`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry SHALL have `consecutive_fails` equal to `3`
- **And** `lifecycle` SHALL be `"paused"`

#### Scenario: scan uses dash when proposal.md has no heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` containing no `# ` heading line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry SHALL have `summary` equal to `"—"` (em dash)

#### Scenario: scan skips non-directory entries in changes dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** the changes directory contains a regular file (not a directory)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result SHALL not contain an entry for that file
