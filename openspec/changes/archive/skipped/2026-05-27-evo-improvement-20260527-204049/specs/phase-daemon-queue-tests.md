# phase-daemon-queue-tests.md

## ADDED Requirements

### Requirement: daemon-queue-scan-tests
The test suite SHALL verify that `_scan_proposal_queue()` correctly scans a changes directory, detects phase progress from output files, and detects lifecycle status from metrics data and `.paused` files.

Note: Basic scanning scenarios (empty dir, nonexistent dir, valid proposal extraction, non-directory skipping, missing proposal.md skipping, sorted results) are already covered in `tests/test_dashboard_api.py::TestScanProposalQueue`. The scenarios below focus on phase detection and lifecycle tracking, which are NOT covered elsewhere.

#### Scenario: scan-detects-clarify-phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `change-a/` with `proposal.md` but no `clarify.md` or `specs/`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `phase` SHALL be `"CLARIFY"`

#### Scenario: scan-detects-enrich-phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `change-b/` with both `proposal.md` and `clarify.md` but no `specs/`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `phase` SHALL be `"ENRICH"`

#### Scenario: scan-detects-implement-phase

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `change-c/` with `proposal.md`, `clarify.md`, and a `specs/` directory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `phase` SHALL be `"IMPLEMENT"`

#### Scenario: scan-proposal-no-heading

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `no-heading/` with a `proposal.md` that has no `# ` heading lines
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `summary` SHALL be `"—"` (the fallback dash)

#### Scenario: scan-paused-from-dot-paused-file

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `paused-change/` with `proposal.md` and a `.paused` file, and `load_all_changes` is mocked to return an empty list
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `paused` SHALL be `True`, `paused_reason` SHALL be `"manual"`, and `lifecycle` SHALL be `"paused"`

#### Scenario: scan-lifecycle-completed-from-metrics

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `done-change/` with `proposal.md`, and `load_all_changes` is mocked to return `[{"change_name": "done-change", "outcome": "success"}]`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `lifecycle` SHALL be `"completed"`

#### Scenario: scan-lifecycle-stuck-from-fail-outcome

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `stuck-change/` with `proposal.md`, and `load_all_changes` is mocked to return `[{"change_name": "stuck-change", "outcome": "fail"}]`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `lifecycle` SHALL be `"stuck"` and `consecutive_fails` SHALL be `1`

#### Scenario: scan-lifecycle-paused-from-consecutive-fails

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `dead-change/` with `proposal.md`, and `load_all_changes` is mocked to return 3 entries for `"dead-change"` all with `outcome="fail"`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `lifecycle` SHALL be `"paused"`, `consecutive_fails` SHALL be `3`, and `paused_reason` SHALL contain `"3 consecutive failures"`

#### Scenario: scan-lifecycle-active-from-running-outcome

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `active-change/` with `proposal.md`, and `load_all_changes` is mocked to return `[{"change_name": "active-change", "outcome": "running"}]`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `lifecycle` SHALL be `"active"`

#### Scenario: scan-default-lifecycle-waiting

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a subdirectory `new-change/` with `proposal.md`, and `load_all_changes` is mocked to return an empty list
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result entry's `lifecycle` SHALL be `"waiting"` and `paused` SHALL be `False`
