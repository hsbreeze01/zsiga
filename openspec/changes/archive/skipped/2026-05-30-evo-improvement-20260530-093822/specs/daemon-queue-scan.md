# daemon-queue-scan.md

## ADDED Requirements

### Requirement: _scan_proposal_queue walks changes directory

`_scan_proposal_queue(changes_dir)` SHALL return a list of dicts, one per
proposal subdirectory that contains a `proposal.md`. Each entry SHALL include
keys `"name"`, `"project"`, `"summary"`, `"phase"`, `"lifecycle"`, `"paused"`,
`"paused_reason"`, and `"consecutive_fails"`.

#### Scenario: non-existent directory returns empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` points to a directory that does not exist
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: empty directory returns empty list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` exists but contains no subdirectories
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: directory without proposal.md is skipped

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` contains a subdirectory `no-proposal/` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: valid proposal directory returns entry with correct keys

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` contains subdirectory `fix-foo/` with `proposal.md` whose first heading line is `# Fix the foo`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list has length 1, and the entry's `"name"` is `"fix-foo"`, `"summary"` is `"Fix the foo"`

#### Scenario: phase detection from file markers

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` contains subdirectory `fix-bar/` with `proposal.md` and `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `"phase"` is `"ENRICH"`

#### Scenario: manual pause via .paused file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue

- **Given** `changes_dir` contains subdirectory `fix-baz/` with `proposal.md` and a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `"paused"` is `True` and `"lifecycle"` is `"paused"`

