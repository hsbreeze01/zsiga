# daemon-proposal-queue

Delta spec for `_scan_proposal_queue(changes_dir)` — walks `openspec/changes/` and returns proposal entries with lifecycle metadata.

## ADDED Requirements

### Requirement: scan-proposal-discovery

`_scan_proposal_queue` SHALL iterate sorted subdirectories of `changes_dir`, read the first `# ...` heading from each `proposal.md` as the summary, and return a list of dicts with keys `name`, `project`, `summary`, `phase`, `lifecycle`, `paused`, `paused_reason`, `consecutive_fails`.

#### Scenario: scan-discovers-proposals

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing subdirectory `my-proposal/` with a valid `proposal.md` whose first heading is `# Fix the thing`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list contains at least one entry with `name == "my-proposal"` and `summary == "Fix the thing"`

#### Scenario: scan-skips-dirs-without-proposal-md

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` containing subdirectory `no-proposal/` that has no `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list does not contain any entry with `name == "no-proposal"`

#### Scenario: scan-empty-changes-dir

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` does not exist as a directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list is empty `[]`

### Requirement: scan-phase-detection

`_scan_proposal_queue` SHALL detect the phase of each proposal based on the presence of output files: only `proposal.md` → `CLARIFY`, `clarify.md` exists → `ENRICH`, `specs/` directory with `.md` files → `IMPLEMENT`.

#### Scenario: scan-phase-clarify-no-artifacts

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory with only `proposal.md` (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase == "CLARIFY"`

#### Scenario: scan-phase-enrich-with-clarify

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory with `proposal.md` and `clarify.md` (no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase == "ENRICH"`

#### Scenario: scan-phase-implement-with-specs

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory with `proposal.md`, `clarify.md`, and `specs/some-spec.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `phase == "IMPLEMENT"`

### Requirement: scan-manual-pause-detection

`_scan_proposal_queue` SHALL check for a `.paused` file in each proposal directory. When present, the entry SHALL have `paused == True`, `lifecycle == "paused"`, and `paused_reason` containing `"manual"`.

#### Scenario: scan-manual-paused-proposal

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory with `proposal.md` and an empty `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused == True` and `paused_reason == "manual"`

### Requirement: scan-default-summary

When `proposal.md` exists but contains no `# ...` heading line, the summary SHALL default to `"—"`.

#### Scenario: scan-proposal-no-heading

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory with `proposal.md` containing only body text without a `# ` heading
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `summary == "—"`

