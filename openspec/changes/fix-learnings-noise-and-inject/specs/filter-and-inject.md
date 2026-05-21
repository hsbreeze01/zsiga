# Spec: Filter Noisy Learnings and Inject into Agent Prompts

## ADDED Requirements

### Requirement: Learnings Write Validation

The system SHALL validate learnings before writing them to `memory/learnings.jsonl` or the `lessons` DB table.

#### Scenario: Empty text learning

- **Given** a learning entry has a `text` field that is empty or has fewer than 10 characters
- **When** the system attempts to record this learning
- **Then** the entry SHALL be silently skipped
- **And** a DEBUG-level log message SHALL be written indicating the skip reason

#### Scenario: daemon.cycle_error pattern

- **Given** a learning entry has a `pattern_key` starting with `daemon.cycle_error`
- **When** the system attempts to record this learning
- **Then** the entry SHALL be silently skipped
- **And** a DEBUG-level log message SHALL be written

#### Scenario: Valid learning

- **Given** a learning entry has `text` with ≥10 characters AND `pattern_key` not starting with `daemon.cycle_error`
- **When** the system records this learning
- **Then** it SHALL be written to both `memory/learnings.jsonl` and the `lessons` DB table

### Requirement: One-time Learnings Cleanup

The system SHALL provide a function `clean_noisy_learnings(base_path)` that removes invalid entries from existing data.

#### Scenario: Cleaning empty-text entries from JSONL

- **Given** `memory/learnings.jsonl` contains entries with empty or <10-char `text` fields
- **When** `clean_noisy_learnings()` is called
- **Then** those entries SHALL be removed from the file
- **And** a summary of removed count SHALL be logged

#### Scenario: Cleaning daemon.cycle_error from JSONL

- **Given** `memory/learnings.jsonl` contains entries with `pattern_key` starting with `daemon.cycle_error`
- **When** `clean_noisy_learnings()` is called
- **Then** those entries SHALL be removed from the file

#### Scenario: Cleaning from DB lessons table

- **Given** the `lessons` DB table contains entries with matching noisy pattern_keys
- **When** `clean_noisy_learnings()` is called
- **Then** those entries SHALL be deleted from the DB

### Requirement: Learnings Injection into IMPLEMENT Prompt

The IMPLEMENT phase SHALL inject relevant past learnings into the agent system prompt.

#### Scenario: Relevant learnings exist for current change

- **Given** `memory/learnings.jsonl` contains entries whose `pattern_key` matches the current change context
- **When** the IMPLEMENT phase builds its system prompt
- **Then** up to 5 most recent relevant learnings SHALL be injected under a `## Previous Learnings (avoid repeating mistakes)` section
- **And** each learning SHALL be formatted as `- [{pattern_key}] {text}`

#### Scenario: No relevant learnings exist

- **Given** no learnings match the current change context
- **When** the IMPLEMENT phase builds its system prompt
- **Then** no learnings section SHALL be injected

### Requirement: Learnings Injection into ENRICH Prompt

The ENRICH phase SHALL inject relevant past learnings into the agent system prompt.

#### Scenario: Relevant learnings exist for current change

- **Given** `memory/learnings.jsonl` contains entries whose `pattern_key` matches the current change context
- **When** the ENRICH phase builds its system prompt
- **Then** up to 3 most recent relevant learnings SHALL be injected under a `## Relevant Past Experience` section

#### Scenario: No relevant learnings exist

- **Given** no learnings match the current change context
- **When** the ENRICH phase builds its system prompt
- **Then** no learnings section SHALL be injected

## REMOVED Requirements

None.
