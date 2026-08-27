# Delta Spec: Proposal Queue Scanning

## ADDED Requirements

### Requirement: scan-proposal-queue

The system SHALL provide `_scan_proposal_queue(changes_dir)` that walks the
given changes directory and returns a list of proposal entry dicts. Each entry
SHALL contain keys: `name`, `project`, `summary`, `phase`, `lifecycle`,
`paused`, `paused_reason`, `consecutive_fails`.

#### Scenario: returns-empty-list-for-nonexistent-dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is a `Path` to a directory that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list `[]`

#### Scenario: skips-entries-without-proposal-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `no-proposal/` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result does not contain any entry with `name == "no-proposal"`

#### Scenario: extracts-summary-from-proposal-heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` whose first `# ` line is `# Fix the thing`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `summary == "Fix the thing"`

#### Scenario: phase-is-clarify-without-clarify-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` but no `clarify.md` and no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `phase == "CLARIFY"`

#### Scenario: phase-is-enrich-with-clarify-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` and `my-change/clarify.md`
- **And** there is no `specs/` directory with `.md` files
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `phase == "ENRICH"`

#### Scenario: phase-is-implement-with-specs-dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` and `my-change/specs/feature.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `phase == "IMPLEMENT"`

#### Scenario: paused-when-dot-paused-file-exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` and `my-change/.paused`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `paused == True`
- **And** `lifecycle == "paused"`
- **And** `paused_reason == "manual"`

#### Scenario: summary-fallback-when-no-heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` with no `# ` line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `summary == "—"`

#### Scenario: skips-non-directory-entries

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a regular file named `not-a-dir.txt`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list (no entry for `not-a-dir.txt`)

#### Scenario: entry-has-all-required-keys

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` with content `# Hello`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the first entry contains all keys: `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`
