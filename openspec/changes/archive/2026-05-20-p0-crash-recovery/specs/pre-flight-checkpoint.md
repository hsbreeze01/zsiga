# Spec: Pre-flight Git Checkpoint

## ADDED Requirements

### REQ-CHK-01: Automatic Checkpoint Before IMPLEMENT

The orchestrator SHALL force-commit any uncommitted changes in the target project
before entering the IMPLEMENT phase, creating a safe rollback point.

#### Scenario: Dirty working tree before IMPLEMENT

- **Given** a change `my-change` is about to enter the IMPLEMENT phase
- **And** the target project has uncommitted changes
- **When** the pre-flight checkpoint logic runs
- **Then** all uncommitted changes SHALL be staged (`git add -A`) and committed with message `"zsiga: checkpoint before my-change"`
- **And** the resulting SHA SHALL be recorded as `pre_sha` for the IMPLEMENT phase

#### Scenario: Clean working tree before IMPLEMENT

- **Given** a change `my-change` is about to enter the IMPLEMENT phase
- **And** the target project has no uncommitted changes
- **When** the pre-flight checkpoint logic runs
- **Then** no additional commit SHALL be made
- **And** the current HEAD SHA SHALL be used as `pre_sha`

### REQ-CHK-02: Checkpoint Combined with WAL Write

The orchestrator SHALL write the Phase WAL at each phase boundary, coupling
checkpoint creation with WAL persistence for crash recovery.

#### Scenario: IMPLEMENT phase entry writes WAL

- **Given** the pre-flight checkpoint is complete with SHA `def456`
- **When** the IMPLEMENT phase begins
- **Then** a `.phase_state` file SHALL be written with `current_phase="implement"` and `pre_sha="def456"`
