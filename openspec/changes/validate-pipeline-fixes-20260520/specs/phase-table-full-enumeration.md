# Delta Spec: Phase Table Full Enumeration

## Context
The dashboard's Phase Performance table (`_phase_table` in `zsiga/metrics/dashboard.py`) currently only renders rows for phases that have recorded data. This means recently-added phases (CLARIFY, ENRICH, OPTIMIZE) may never appear until they accumulate data, making it impossible to verify the pipeline covers all phases.

## ADDED Requirements

### Requirement: All Phase enum values SHALL appear in phase table output

`_phase_table` SHALL iterate over every member of the Phase enum and produce a row for each, regardless of whether any metrics data exists for that phase.

#### Scenario: Phase with recorded data
- **Given** the Phase enum contains the value `IMPLEMENT`
- **And** there are 3 completed IMPLEMENT phase records in the database
- **When** `_phase_table` is called
- **Then** the output row for `IMPLEMENT` SHALL display the correct count (3)

#### Scenario: Phase with no recorded data
- **Given** the Phase enum contains the value `CLARIFY`
- **And** there are 0 completed CLARIFY phase records in the database
- **When** `_phase_table` is called
- **Then** the output row for `CLARIFY` SHALL still appear with a count of 0

#### Scenario: Enum-driven ordering
- **Given** the Phase enum defines values in a specific order
- **When** `_phase_table` is called
- **Then** rows SHALL appear in the same order as the Phase enum definition

### Requirement: Missing-data phases MUST display zero values

Any phase row that has no corresponding data in the database MUST show numeric fields (count, duration, etc.) as `0` rather than being omitted entirely.

#### Scenario: All numeric fields default to zero
- **Given** the Phase enum contains the value `OPTIMIZE`
- **And** no OPTIMIZE records exist
- **When** `_phase_table` renders the OPTIMIZE row
- **Then** count SHALL be `0`
- **And** any average-duration field SHALL be `0` or `N/A`

## MODIFIED Requirements

_(None)_

## REMOVED Requirements

_(None)_
