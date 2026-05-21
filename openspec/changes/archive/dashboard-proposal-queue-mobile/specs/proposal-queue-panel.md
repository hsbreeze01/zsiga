# Spec: Proposal Queue Panel (Unified Rendering)

## ADDED Requirements

### Requirement: Unified Proposal Queue Panel

The dashboard SHALL render a single Proposal Queue panel containing two sub-sections — "Current" and "Queued" — entirely from Python-side data, replacing the previous static placeholder and client-side JS rendering approach.

#### Scenario: Daemon is actively processing a proposal

- **Given** `data/daemon_state.json` exists and contains a non-empty `current_change` field
- **And** `current_phase` is set to one of the known phase names
- **When** the dashboard HTML is generated
- **Then** the "Current" sub-section SHALL display the proposal name, associated project, current phase name, and heartbeat-derived start time
- **And** the "Queued" sub-section SHALL list all other proposals found in `openspec/changes/` directories (excluding the currently active one)

#### Scenario: No active proposal (daemon idle)

- **Given** `data/daemon_state.json` does not exist or contains an empty/null `current_change` field
- **When** the dashboard HTML is generated
- **Then** the "Current" sub-section SHALL display "💤 Idle" as a fallback state
- **And** the "Queued" sub-section SHALL still render if other proposals exist in `openspec/changes/`

#### Scenario: No queued proposals

- **Given** `openspec/changes/` contains no proposal directories (or no directories with a valid `proposal.md`)
- **When** the dashboard HTML is generated
- **Then** the "Queued" sub-section SHALL display "Queue empty"
- **And** the "Current" sub-section SHALL still render based on daemon state

#### Scenario: daemon_state.json is missing or malformed

- **Given** `data/daemon_state.json` does not exist or cannot be parsed as valid JSON
- **When** the dashboard HTML is generated
- **Then** generation SHALL NOT fail — it SHALL gracefully degrade by treating the daemon as idle
- **And** the "Current" sub-section SHALL display the idle state

### Requirement: Queued Proposal Listing

Each queued proposal entry SHALL display: a sequential index number, the proposal name (extracted from `proposal.md` first-line heading), the associated project name, and a one-line summary.

#### Scenario: Multiple proposals in queue

- **Given** `openspec/changes/` contains 3 proposal directories each with a `proposal.md`
- **And** one of them is the currently active proposal
- **When** the dashboard HTML is generated
- **Then** the "Queued" sub-section SHALL display exactly 2 entries
- **And** each entry SHALL show its 1-based index, name, project, and summary

#### Scenario: Proposal directory without proposal.md

- **Given** an `openspec/changes/` sub-directory exists but does not contain a `proposal.md`
- **When** the dashboard scans for queued proposals
- **Then** that directory SHALL be silently skipped without causing errors

## REMOVED Requirements

### Requirement: Remove Static Proposal Queue Placeholder

The dashboard HTML SHALL NOT contain a `{proposal_queue_section}` template variable placeholder for proposal queue content. All queue content SHALL be fully rendered inline.

#### Scenario: Dashboard generation with queue data

- **Given** any dashboard generation invocation
- **When** the output HTML is inspected
- **Then** the string `{proposal_queue_section}` SHALL NOT appear anywhere in the generated HTML

### Requirement: Remove JS-driven Queue Section

The dashboard HTML SHALL NOT contain a `<div id="queue-section">` element, and SHALL NOT contain any JavaScript `fetch('/api/status.json', ...)` calls or `updateQueueSection` function definitions.

#### Scenario: Dashboard generation produces no dead JS

- **Given** any dashboard generation invocation
- **When** the output HTML is inspected
- **Then** the string `id="queue-section"` SHALL NOT appear
- **And** the string `fetch('/api/status.json'` SHALL NOT appear
- **And** the string `updateQueueSection` SHALL NOT appear
