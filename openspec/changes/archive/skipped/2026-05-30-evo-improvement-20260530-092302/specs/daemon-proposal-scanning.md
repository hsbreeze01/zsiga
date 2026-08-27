# daemon-proposal-scanning.md — Proposal Queue Scanning

## ADDED Requirements

### Requirement: scan_proposal_queue_walks_changes_dir
`_scan_proposal_queue(changes_dir)` SHALL walk the given directory and return a list of dicts, one per subdirectory that contains a `proposal.md`. Each entry SHALL contain keys `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`.

#### Scenario: scan_empty_directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** an empty directory as `changes_dir`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: scan_dir_without_proposal_md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a directory containing a subdirectory with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the subdirectory is skipped and the result is `[]`

#### Scenario: scan_single_valid_proposal

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a directory containing a subdirectory `my-change` with `proposal.md` whose first heading line is `# My Great Proposal`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list has length 1, the entry's `name` is `"my-change"`, and `summary` is `"My Great Proposal"`

#### Scenario: scan_detects_clarify_phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `proposal.md` but no `clarify.md` and no `specs/` dir
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"CLARIFY"`

#### Scenario: scan_detects_enrich_phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `proposal.md` and `clarify.md` but no `specs/` dir
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"ENRICH"`

#### Scenario: scan_detects_implement_phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `proposal.md`, `clarify.md`, and a `specs/` dir containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"IMPLEMENT"`

#### Scenario: scan_nonexistent_dir_returns_empty

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a path that does not exist on disk
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: scan_skips_files_not_dirs

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a directory containing both a plain file and a subdirectory with `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** only the subdirectory entry appears in the result
