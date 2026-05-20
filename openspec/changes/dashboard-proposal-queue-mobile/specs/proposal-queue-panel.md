# Delta Spec: Proposal Queue Panel

## MODIFIED Requirements

### REQ-PQ-001: Unified Proposal Queue Rendering

The dashboard SHALL render a single Proposal Queue panel via Python server-side template substitution, replacing the former dual-block approach (static `<div class="section"><h2>📋 Proposal Queue</h2>` table + empty `<div id="queue-section">`).

#### Scenario: Dashboard renders unified queue panel
- **Given** the dashboard HTML template contains a `{proposal_queue_section}` placeholder
- **When** the Python dashboard builder generates the final HTML
- **Then** the placeholder SHALL be replaced with a complete queue panel HTML fragment containing two sub-sections: "Current" and "Queued"
- **And** the output SHALL NOT contain a standalone `<div class="section">` with a static Proposal Queue table
- **And** the output SHALL NOT contain a `<div id="queue-section">` element
- **And** the output SHALL NOT contain any `updateQueueSection` JavaScript function

---

### REQ-PQ-002: Current Proposal Sub-Panel

The queue panel SHALL display a "Current" sub-section showing the proposal currently being processed by the daemon.

#### Scenario: Daemon is actively processing a proposal
- **Given** `daemon_state.json` exists and contains `current_change` with a non-empty value
- **And** the file contains `current_phase` and `heartbeat` fields
- **When** the dashboard builder renders the queue panel
- **Then** the Current sub-section SHALL display:
  - the proposal name (derived from `current_change`)
  - the associated project identifier
  - a phase progress bar with eight stages (REQ-PHASE-001)
  - the current phase visually highlighted
  - the heartbeat timestamp
- **And** no error or exception SHALL be raised

#### Scenario: Daemon is idle (no current proposal)
- **Given** `daemon_state.json` does not exist OR `current_change` is empty or absent
- **When** the dashboard builder renders the queue panel
- **Then** the Current sub-section SHALL display an Idle state indicator
- **And** no error or exception SHALL be raised

---

### REQ-PQ-003: Queued Proposals Sub-Panel

The queue panel SHALL display a "Queued" sub-section listing all proposals awaiting processing.

#### Scenario: One or more proposals are queued
- **Given** the `openspec/changes/` directory contains one or more proposal subdirectories
- **And** each subdirectory contains a `proposal.md` file
- **When** the dashboard builder renders the queue panel
- **Then** the Queued sub-section SHALL display each proposal with:
  - a sequential index number
  - the proposal name (directory name or extracted title from `proposal.md` first heading)
  - the associated project identifier
  - a one-line summary extracted from the first heading line (`# ...`) of `proposal.md`
- **And** the proposal currently being processed (matching `current_change`) SHALL NOT appear in the queued list

#### Scenario: No proposals are queued
- **Given** the `openspec/changes/` directory is empty or contains no valid proposal subdirectories
- **When** the dashboard builder renders the queue panel
- **Then** the Queued sub-section SHALL display "Queue empty"
- **And** no error SHALL be raised

#### Scenario: Proposal directory has missing or malformed proposal.md
- **Given** a proposal subdirectory exists but `proposal.md` is absent or has no heading line
- **When** the dashboard builder scans the directory
- **Then** the proposal SHALL still be listed with the directory name as fallback
- **And** the summary field SHALL be an empty string or a placeholder
- **And** no exception SHALL be raised

#### Scenario: Non-proposal items in changes directory
- **Given** the `openspec/changes/` directory contains files (not directories) or hidden items (prefixed with `.`)
- **When** the dashboard builder scans the directory
- **Then** these items SHALL be skipped and not listed as proposals
- **And** only subdirectories containing `proposal.md` SHALL be considered valid proposals
