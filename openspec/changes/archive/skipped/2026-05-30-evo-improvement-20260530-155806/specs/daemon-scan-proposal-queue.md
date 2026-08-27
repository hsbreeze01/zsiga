# daemon-scan-proposal-queue

## ADDED Requirements

### Requirement: _scan_proposal_queue handles empty and missing directories

When the changes directory does not exist or contains no subdirectories with
`proposal.md`, `_scan_proposal_queue()` SHALL return an empty list.

#### Scenario: Returns empty list for non-existent directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is set to a non-existent path
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: Returns empty list for directory with no proposal.md files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing only subdirectories without `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: Skips non-directory entries in changes_dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing a regular file and a directory with `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** only the directory entry appears in the result, the regular file is skipped

### Requirement: _scan_proposal_queue extracts proposal metadata

For each subdirectory containing `proposal.md`, the function SHALL return an
entry with `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`,
`paused_reason`, and `consecutive_fails` keys.

#### Scenario: Extracts summary from first # heading in proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory `my-change/` with `proposal.md` whose first line is `# Fix logging bug`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry for `my-change` has `summary` equal to `"Fix logging bug"`

#### Scenario: Summary defaults to dash when no heading found

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` containing no `# ` heading lines
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `summary` is `"—"`

#### Scenario: Phase is CLARIFY when no clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with only `proposal.md` (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"CLARIFY"`

#### Scenario: Phase is ENRICH when clarify.md exists but no specs

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` and `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"ENRICH"`

#### Scenario: Phase is IMPLEMENT when specs dir contains md files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md`, `clarify.md`, and `specs/` containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"IMPLEMENT"`

#### Scenario: Proposal marked as paused when .paused file exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a change directory with `proposal.md` and a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused` equal to `True` and `lifecycle` equal to `"paused"`

### Requirement: _scan_proposal_queue sorts entries by name

The returned list SHALL be sorted alphabetically by directory name, matching
the `sorted(changes_dir.iterdir())` order.

#### Scenario: Entries are sorted alphabetically

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** change directories `beta-change/`, `alpha-change/`, and `gamma-change/` each with `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entries appear in order `alpha-change`, `beta-change`, `gamma-change`
