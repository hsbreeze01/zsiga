# daemon-proposal-scan

## ADDED Requirements

### Requirement: Scan proposal queue from changes directory

`_scan_proposal_queue(changes_dir)` SHALL walk the given changes directory and
return a list of dicts, each with keys `"name"`, `"project"`, `"summary"`,
`"phase"`, `"lifecycle"`, `"paused"`, `"paused_reason"`, `"consecutive_fails"`.
It SHALL skip non-directory entries and directories without `proposal.md`.

#### Scenario: Empty directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is an empty directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: Non-existent directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a path that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: Directory with proposal.md returns entry with summary

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `my-proposal` with a `proposal.md` whose first `# ` line reads `# Fix the bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is a list of length 1; the first entry has `"name": "my-proposal"` and `"summary": "Fix the bug"`

#### Scenario: Directories without proposal.md are skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains subdirectories `a` (with `proposal.md`) and `b` (without `proposal.md`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list has exactly 1 entry with `"name": "a"`

#### Scenario: Phase detection from output files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `"phase"` is `"ENRICH"`

#### Scenario: Phase advances to IMPLEMENT when specs exist

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains both `clarify.md` and a `specs/` directory with at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `"phase"` is `"IMPLEMENT"`

#### Scenario: Paused lifecycle when .paused file exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called (with metrics mocked to return no records)
- **Then** the entry's `"paused"` is `True` and `"lifecycle"` is `"paused"`

#### Scenario: Summary defaults to em-dash when no heading found

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory has `proposal.md` with no `# ` heading line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `"summary"` is `"—"`
