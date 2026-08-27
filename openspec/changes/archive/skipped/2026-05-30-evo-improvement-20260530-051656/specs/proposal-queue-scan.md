# proposal-queue-scan

## ADDED Requirements

### Requirement: _scan_proposal_queue SHALL enumerate proposal directories

`_scan_proposal_queue()` SHALL walk the `openspec/changes/` directory
(or a provided override) and return a list of dicts, one per valid
proposal directory that contains `proposal.md`.

#### Scenario: returns empty list for non-existent changes_dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a path that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result SHALL be an empty list `[]`

#### Scenario: skips directories without proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a subdirectory `no-proposal/` with no
  `proposal.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result SHALL not contain any entry with `name == "no-proposal"`

#### Scenario: extracts summary from first markdown heading in proposal.md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `my-change/proposal.md` whose first
  `# ...` line reads `# Fix memory leak`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry with `name == "my-change"` SHALL have
  `summary == "Fix memory leak"`

#### Scenario: skips non-directory entries in changes_dir

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a regular file named `README.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result SHALL not contain any entry with `name == "README.md"`

#### Scenario: marks entry as paused when .paused file exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `paused-change/proposal.md` and
  `paused-change/.paused`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry with `name == "paused-change"` SHALL have
  `paused == True` and `lifecycle == "paused"`

#### Scenario: detects phase based on output file presence

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains `spec-change/proposal.md` and
  `spec-change/clarify.md` and `spec-change/specs/some.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry with `name == "spec-change"` SHALL have
  `phase == "IMPLEMENT"` (because both clarify.md and specs/ exist)

#### Scenario: each entry has required keys

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains at least one valid proposal directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** every entry SHALL contain the keys `name`, `project`, `summary`,
  `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`
