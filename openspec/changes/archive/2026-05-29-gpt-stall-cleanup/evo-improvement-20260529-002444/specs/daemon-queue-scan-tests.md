# daemon-queue-scan-tests

## ADDED Requirements

### Requirement: _scan_proposal_queue SHALL enumerate proposals with metadata

`_scan_proposal_queue()` SHALL walk the changes directory and return a list of
 dicts, one per proposal sub-directory that contains a `proposal.md`. Each
 entry SHALL include `name`, `project`, `summary`, `phase`, `lifecycle`,
 `paused`, `paused_reason`, and `consecutive_fails` keys.

#### Scenario: scan returns empty list when directory missing

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** the `changes_dir` does not exist on disk
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: scan skips directories without proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains sub-directories `alpha/` (with `proposal.md`) and `beta/` (no `proposal.md`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list has length 1
- **And** the single entry's `name` is `"alpha"`

#### Scenario: scan extracts summary from first heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir/alpha/proposal.md` starts with a line `# Fix the bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `alpha` has `summary` equal to `"Fix the bug"`

#### Scenario: scan detects CLARIFY phase when only proposal.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir/alpha/` contains only `proposal.md` (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `alpha` has `phase` equal to `"CLARIFY"`

#### Scenario: scan detects ENRICH phase when clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir/alpha/` contains `proposal.md` and `clarify.md` (no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `alpha` has `phase` equal to `"ENRICH"`

#### Scenario: scan detects IMPLEMENT phase when specs/ with .md files exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir/alpha/` contains `proposal.md`, `clarify.md`, and `specs/foo.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `alpha` has `phase` equal to `"IMPLEMENT"`

#### Scenario: scan marks proposal paused when .paused file exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir/alpha/` contains `proposal.md` and `.paused`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry for `alpha` has `paused` equal to `True`
- **And** `lifecycle` equal to `"paused"`

#### Scenario: scan skips non-directory entries

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a regular file `notes.txt` alongside `alpha/proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list has length 1 (only `alpha`)
