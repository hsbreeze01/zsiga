# Spec: Proposal Queue Panel

## ADDED Requirements

### Requirement: Proposal Queue Rendering

The dashboard SHALL display a "📋 Proposal Queue" section that shows all pending proposals across all configured target projects.

#### Scenario: Multiple proposals queued across projects

- Given the daemon is configured with target projects `factory` and `compass`
- And `factory` has two proposal directories under `openspec/changes/` (excluding `archive`)
- And `compass` has one proposal directory under `openspec/changes/` (excluding `archive`)
- When `generate_dashboard()` is called
- Then the rendered HTML SHALL contain a `<h2>📋 Proposal Queue</h2>` section
- And the section SHALL display a table with three rows (one per proposal)
- And each row SHALL show the proposal name, project name, and summary

#### Scenario: No proposals in queue

- Given no target projects have any proposal directories under `openspec/changes/`
- When `generate_dashboard()` is called
- Then the queue section SHALL display "Queue empty — idle polling"

#### Scenario: Proposal summary extraction

- Given a proposal directory `my-feature` exists with a `proposal.md` whose first non-empty line starts with `# `
- When the queue panel is rendered
- Then the summary column SHALL display the text of that first heading line (without the `# ` prefix)
- If `proposal.md` is missing or has no heading line, the summary SHALL display "—"

### Requirement: Current Processing Highlight

The queue panel SHALL visually highlight the proposal currently being processed by the daemon.

#### Scenario: Daemon actively processing a proposal

- Given `data/daemon_state.json` contains `current_change: "add-auth"`, `current_phase: "implement"`, `current_project: "factory"`
- And proposal `add-auth` exists in the queue
- When the queue table is rendered
- Then the row for `add-auth` SHALL have a distinct left-border highlight (e.g. `border-left: 3px solid #f59e0b`)
- And the row SHALL display a phase badge showing "implement"

#### Scenario: Daemon idle, no current change

- Given `data/daemon_state.json` contains `current_change: null`
- When the queue table is rendered
- Then no rows SHALL be highlighted
- And no phase badges SHALL appear in any row

### Requirement: Queue Section Placement

The proposal queue section SHALL be placed between the daemon status section and the "Phase Performance" section in the dashboard layout.

#### Scenario: Dashboard layout ordering

- Given the dashboard is fully rendered
- When viewing the HTML output
- Then the "📋 Proposal Queue" section SHALL appear after the daemon status cards
- And the "📋 Proposal Queue" section SHALL appear before the "⚡ Phase Performance" section

### Requirement: Cross-Target Proposal Scanning

The queue panel SHALL scan proposals from all configured target projects, including remote (SSH) targets.

#### Scenario: Remote target with proposals

- Given target `factory` uses SSH transport
- And the remote host has proposals under its `openspec/changes/` directory
- When `generate_dashboard()` scans for proposals
- Then the queue panel SHALL include those remote proposals using the existing transport abstraction
- And each remote proposal row SHALL show the correct project name

#### Scenario: Local target proposals

- Given a local target project path exists on the filesystem
- And it has proposal directories under `openspec/changes/`
- When scanning for proposals
- Then those proposals SHALL be discovered via direct filesystem access

### Requirement: Performance Budget

Proposal queue scanning SHALL NOT significantly delay dashboard generation.

#### Scenario: Large number of proposals

- Given 20+ proposal directories exist across targets
- When `generate_dashboard()` runs
- Then the queue scanning and rendering SHALL complete within 5 seconds
- And only the first line of each `proposal.md` SHALL be read (not the entire file)
