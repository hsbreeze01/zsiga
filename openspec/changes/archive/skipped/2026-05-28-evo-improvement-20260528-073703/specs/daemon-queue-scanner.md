# daemon-queue-scanner

## ADDED Requirements

### Requirement: Scan proposal queue from changes directory

`_scan_proposal_queue(changes_dir)` SHALL walk the given `changes_dir`
and return a list of proposal dicts sorted by directory name. Each dict
SHALL contain keys `name`, `project`, `summary`, `phase`, `lifecycle`,
`paused`, `paused_reason`, `consecutive_fails`.

Only subdirectories that contain a `proposal.md` file SHALL be included.

#### Scenario: Returns empty list for non-existent directory

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a path that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list `[]`

#### Scenario: Skips subdirectories without proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains subdirectory `no-proposal/` with no
  `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is an empty list (no entries for `no-proposal`)

#### Scenario: Extracts summary from first heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` whose first
  `# ...` line is `# Fix the logging bug`
- **When** `_scan_proposal_queue(changes_dir)` is called (with `load_config` mocked to raise)
- **Then** the returned entry has `summary` equal to `"Fix the logging bug"`

#### Scenario: Phase detection defaults to CLARIFY

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains only `proposal.md` (no
  `clarify.md`, no `specs/` directory)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `phase` equal to `"CLARIFY"`

#### Scenario: Phase detection upgrades to ENRICH when clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `proposal.md` and `clarify.md`
  but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `phase` equal to `"ENRICH"`

#### Scenario: Phase detection upgrades to IMPLEMENT when specs exist

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `proposal.md`, `clarify.md`,
  and `specs/` with at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `phase` equal to `"IMPLEMENT"`

#### Scenario: Consecutive fails counted from metrics tail

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `load_all_changes()` returns records for `my-change` where
  the last 3 entries have `outcome="fail"` (with `load_config` mocked to
  raise)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `consecutive_fails` equal to `3`
  and `lifecycle` equal to `"paused"`

#### Scenario: Manual .paused file forces paused state

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `proposal.md` and `.paused`
  (with `load_config` and `load_all_changes` mocked to raise)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `paused` equal to `True` and
  `paused_reason` equal to `"manual"`

#### Scenario: Project falls back to directory name

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `load_config()` raises an exception
- **When** `_scan_proposal_queue(changes_dir)` is called for a directory
  named `my-awesome-change`
- **Then** the returned entry has `project` equal to `"my-awesome-change"`

#### Scenario: Proposal name equals directory name

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `foo-bar/proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned entry has `name` equal to `"foo-bar"`
