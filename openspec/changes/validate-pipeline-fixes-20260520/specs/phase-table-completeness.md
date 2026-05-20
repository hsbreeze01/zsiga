# Delta Spec: Phase Table Completeness

## Context
The dashboard's Phase Performance table (`_phase_table` in `zsiga/metrics/dashboard.py`) currently only renders rows for phases that have recorded data. Recently-added phases (CLARIFY, ENRICH, OPTIMIZE) are invisible until they accumulate data, making it impossible to verify the pipeline covers all stages.

## MODIFIED Requirements

### Requirement: Phase Performance Table Shows All Enum Values

`_phase_table` SHALL iterate over every member of the Phase enum and produce one table row for each, regardless of whether any metrics data exists for that phase.

#### Scenario: Phase with recorded data

- **Given** the Phase enum contains the value `IMPLEMENT`
- **And** there are 3 completed IMPLEMENT phase records in the database
- **When** `_phase_table` is called
- **Then** the output row for `IMPLEMENT` SHALL display the correct count (3)
- **And** average-duration and other numeric fields SHALL reflect actual recorded values

#### Scenario: Phase with no recorded data

- **Given** the Phase enum contains the value `CLARIFY`
- **And** there are 0 completed CLARIFY phase records in the database
- **When** `_phase_table` is called
- **Then** the output row for `CLARIFY` SHALL appear with `count=0`
- **And** all other numeric fields (duration, average, etc.) SHALL display `0` or equivalent zero-sentinel
- **And** no `KeyError` or other exception SHALL be raised

#### Scenario: Completely empty metrics dict

- **Given** the Phase enumeration contains all eight values
- **And** the timing records dict is empty `{}`
- **When** `_phase_table` is called
- **Then** the rendered table SHALL contain one row per Phase value, each showing `count=0`
- **And** no exception SHALL be raised

#### Scenario: Enum-driven ordering

- **Given** the Phase enum defines values in a specific order
- **When** `_phase_table` is called
- **Then** rows SHALL appear in the same order as the Phase enum definition

#### Scenario: Future extensibility

- **Given** a future change adds a new value to the Phase enumeration
- **When** `_phase_table` is called
- **Then** the new phase SHALL appear in the rendered table without any code change to `_phase_table` itself
- **Note** This is a SHOULD constraint — the function SHOULD iterate the enum dynamically rather than hard-code phase names

## ADDED Requirements

_(None)_

## REMOVED Requirements

_(None)_
