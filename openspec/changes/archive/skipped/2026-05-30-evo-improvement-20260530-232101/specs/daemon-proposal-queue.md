# daemon-proposal-queue

## ADDED Requirements

### Requirement: _scan_proposal_queue SHALL detect phase from output files

`_scan_proposal_queue(changes_dir)` SHALL set the `phase` field of each entry
based on the presence of output files:
- `"CLARIFY"` when neither `clarify.md` nor `specs/*.md` exist
- `"ENRICH"` when `clarify.md` exists but no `specs/*.md` files
- `"IMPLEMENT"` when `specs/*.md` files exist

#### Scenario: no output files yields CLARIFY phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** a change directory with only `proposal.md` (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` equals `"CLARIFY"`

#### Scenario: clarify.md present yields ENRICH phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** a change directory with `proposal.md` and `clarify.md` (no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` equals `"ENRICH"`

#### Scenario: specs directory with md files yields IMPLEMENT phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** a change directory with `proposal.md`, `clarify.md`, and `specs/feature.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` equals `"IMPLEMENT"`

### Requirement: _scan_proposal_queue SHALL detect .paused marker file

When a `.paused` file exists in a change directory, the entry SHALL have
`paused` set to `True` and `lifecycle` set to `"paused"`. The `paused_reason`
SHALL be `"manual"` unless already set by a metrics-based reason.

#### Scenario: .paused file sets paused flag

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** a change directory with `proposal.md` and `.paused`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `paused` is `True`
- **And** the entry's `lifecycle` equals `"paused"`
- **And** the entry's `paused_reason` equals `"manual"`

### Requirement: _scan_proposal_queue SHALL return structured entries

Each entry returned by `_scan_proposal_queue` SHALL contain keys `name`,
`project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, and
`consecutive_fails`. The `name` SHALL match the directory name, and `summary`
SHALL be extracted from the first `# ` heading line in `proposal.md`, falling
back to `"—"` when no heading is found.

#### Scenario: entry has all required keys

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** a change directory named `my-change` with `proposal.md` containing `"# Fix auth\n"`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry dict contains all keys: `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`
- **And** `entry["name"]` equals `"my-change"`
- **And** `entry["summary"]` equals `"Fix auth"`

#### Scenario: non-directory entries are skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` contains a regular file named `readme.txt`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list

#### Scenario: directory without proposal.md is skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` contains a subdirectory `no-proposal` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list
