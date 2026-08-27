# daemon-proposal-queue-scan

## ADDED Requirements

### Requirement: scan-empty-or-missing-directory
`_scan_proposal_queue(changes_dir)` SHALL return an empty list when the
`changes_dir` does not exist or is not a directory.

#### Scenario: non-existent-directory-returns-empty

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a path that does not exist on disk
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

#### Scenario: file-as-changes-dir-returns-empty

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` points to a regular file (not a directory)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** it returns `[]`

---

### Requirement: scan-skips-invalid-entries
`_scan_proposal_queue` SHALL skip entries that are not directories or that
do not contain a `proposal.md` file.  Entries without `proposal.md` MUST NOT
appear in the returned queue.

#### Scenario: skips-non-directory-entries

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains a regular file named `readme.txt`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result does not contain any entry with `name == "readme.txt"`

#### Scenario: skips-dir-without-proposal-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` has a subdirectory `no-proposal/` with no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result does not contain an entry with `name == "no-proposal"`

---

### Requirement: scan-extracts-summary
For each valid proposal directory containing `proposal.md`, `_scan_proposal_queue`
SHALL extract the first `# ` heading line as the `summary` field.  If no such
heading exists, summary SHALL default to `"—"`.

#### Scenario: extracts-first-heading-as-summary

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory whose `proposal.md` starts with `# My Great Proposal`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `summary == "My Great Proposal"`

#### Scenario: no-heading-defaults-dash

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory whose `proposal.md` contains no `# ` line
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the matching entry has `summary == "—"`

---

### Requirement: scan-phase-detection
`_scan_proposal_queue` SHALL detect the current phase of each proposal based on
output files: no `clarify.md` → `"CLARIFY"`, `clarify.md` present but no specs
→ `"ENRICH"`, specs directory with `.md` files → `"IMPLEMENT"`.

#### Scenario: phase-is-clarify-when-no-clarity-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has only `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase == "CLARIFY"`

#### Scenario: phase-is-enrich-when-clarity-md-exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `proposal.md` and `clarify.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase == "ENRICH"`

#### Scenario: phase-is-implement-when-specs-dir-has-md

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that has `proposal.md`, `clarify.md`, and a `specs/` directory containing at least one `.md` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase == "IMPLEMENT"`

---

### Requirement: scan-lifecycle-detection
`_scan_proposal_queue` SHALL detect lifecycle status from metrics DB records.
Lifecycle MUST be `"waiting"` when no DB records exist, `"completed"` when the
last outcome is `"success"`, `"stuck"` when the last outcome is `"fail"` or
`"reverted"` (with fewer than 3 consecutive failures), and `"paused"` when
consecutive failures reach 3 or more.  A `.paused` file in the proposal
directory SHALL override lifecycle to `"paused"` regardless of DB state.

#### Scenario: no-db-records-lifecycle-waiting

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory and `load_all_changes` returns no matching records
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `lifecycle == "waiting"` and `consecutive_fails == 0`

#### Scenario: success-outcome-lifecycle-completed

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory and `load_all_changes` returns one record with `outcome == "success"` matching the proposal name
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `lifecycle == "completed"`

#### Scenario: consecutive-fails-triggers-paused

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory and `load_all_changes` returns 3 consecutive records with `outcome == "fail"` matching the proposal name
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `lifecycle == "paused"` and `paused == True`

#### Scenario: paused-file-overrides-lifecycle

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory that contains a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused == True` and `lifecycle == "paused"`

---

### Requirement: scan-entry-structure
Each entry returned by `_scan_proposal_queue` SHALL be a dictionary containing
the keys `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`,
`paused_reason`, and `consecutive_fails`.

#### Scenario: entry-has-all-required-keys

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a valid proposal directory with `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the first entry contains all keys: `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`
