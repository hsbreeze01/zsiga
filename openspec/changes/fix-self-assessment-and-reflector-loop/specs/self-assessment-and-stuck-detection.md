# Spec: Self-Assessment Recording and Auto-Proposal Stuck Detection

## ADDED Requirements

### Requirement: Self-Assessment Recording on REFLECT

The REFLECT phase SHALL write a self-assessment record to the database after every change completion.

#### Scenario: Successful change completion

- **Given** a change has completed with outcome `success`
- **When** the REFLECT phase executes
- **Then** a self_assessment record SHALL be written to the database
- **And** the record SHALL contain: change_name, outcome, reflection_text, lessons_learned, timestamp

#### Scenario: Reverted change

- **Given** a change has completed with outcome `reverted`
- **When** the REFLECT phase executes
- **Then** a self_assessment record SHALL be written with the failure analysis

#### Scenario: REFLECT phase fails to write assessment

- **Given** the self_assessment write fails (DB error, schema mismatch, etc.)
- **When** the REFLECT phase catches the error
- **Then** a WARNING log SHALL be written
- **And** the pipeline SHALL NOT crash

### Requirement: Auto-Proposal Stuck Detection

The Reflector SHALL detect when an auto-generated proposal has failed verification multiple times and stop regenerating it.

#### Scenario: Same proposal pattern failed 3+ times

- **Given** the last 3 auto-proposals with the same pattern_key all have outcome `reverted`
- **When** the Reflector considers generating a new proposal with that pattern_key
- **Then** the Reflector SHALL NOT generate the proposal
- **And** the Reflector SHALL create a `diagnosis.md` file in `openspec/changes/auto-stuck-{pattern_key}-{date}/`

#### Scenario: Diagnosis file content

- **Given** a stuck pattern has been detected
- **When** the diagnosis.md is generated
- **Then** it SHALL contain: list of failed proposal names, failure reasons from phase_records, and suggested human intervention directions

#### Scenario: Diagnosis does not trigger pipeline

- **Given** a `diagnosis.md` file exists without a `proposal.md`
- **When** the daemon scans for proposals
- **Then** that directory SHALL be skipped

### Requirement: Reflector History-Aware Proposal Generation

The Reflector SHALL inject recent failure history when generating new proposals.

#### Scenario: Previous failures exist for a pattern

- **Given** there are recent failed changes with a matching pattern
- **When** the Reflector renders a proposal template
- **Then** the last 3 failure reasons SHALL be included in the proposal context
- **And** the generated proposal SHALL reference past failures to avoid repeating the same approach

## REMOVED Requirements

None.
