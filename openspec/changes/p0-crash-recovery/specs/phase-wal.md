# Spec: Phase Write-Ahead Log

## ADDED Requirements

### REQ-WAL-01: Phase State Persistence

The system SHALL persist the current pipeline phase state to a `.phase_state` file
inside the change directory at every phase boundary (enrich, implement, verify, deliver).

#### Scenario: Write WAL at phase boundary

- **Given** a change is being processed with change_dir `/repo/openspec/changes/my-change`
- **When** the orchestrator enters the IMPLEMENT phase with pre_sha `abc123` and target_path `/repo`
- **Then** a file `.phase_state` SHALL be written to the change directory containing JSON:
  ```json
  {
    "current_phase": "implement",
    "started_at": "2025-01-15T10:30:00",
    "pre_sha": "abc123",
    "target_path": "/repo",
    "project": "my-project"
  }
  ```
- **And** the file SHALL be readable by the crash recovery scanner

#### Scenario: WAL is deleted on successful DELIVER

- **Given** a change has `.phase_state` in its directory
- **When** the DELIVER phase completes successfully
- **Then** the `.phase_state` file SHALL be deleted

#### Scenario: WAL is deleted on REVERT

- **Given** a change has `.phase_state` in its directory
- **When** the pipeline reverts the change (verify fail, implement fail, escalation abort)
- **Then** the `.phase_state` file SHALL be deleted

### REQ-WAL-02: Phase WAL Module API

The system SHALL provide a `PhaseWAL` class in `pipeline/phase_wal.py` with the following interface:

#### Scenario: Write and read round-trip

- **Given** a `PhaseWAL` instance with a change_dir and transport
- **When** `write(phase="implement", pre_sha="abc123", target_path="/repo", project="my-project")` is called
- **Then** `read()` SHALL return a dict with keys `current_phase`, `started_at`, `pre_sha`, `target_path`, `project`
- **And** `exists()` SHALL return `True`

#### Scenario: Delete WAL

- **Given** a PhaseWAL with an existing `.phase_state` file
- **When** `delete()` is called
- **Then** `exists()` SHALL return `False`
- **And** `read()` SHALL return `None`

#### Scenario: Read non-existent WAL

- **Given** a PhaseWAL whose change_dir has no `.phase_state`
- **When** `read()` is called
- **Then** it SHALL return `None`
