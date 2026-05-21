# Spec: Phase Table Completeness

## ADDED Requirements

### Requirement: All Phase enum members SHALL appear in phase table output

The `_phase_table` function in `zsiga/metrics/dashboard.py` SHALL iterate over every member of the Phase enum when constructing the phase performance table, rather than only emitting rows for phases that have recorded data.

#### Scenario: Table includes phases with no recorded data

- **Given** the Phase enum defines members including at minimum CLARIFY, ENRICH, IMPLEMENT, REVIEW, VERIFY, OPTIMIZE, REFLECT, and DELIVER
- **And** some enum members have zero recorded executions in the metrics data
- **When** `_phase_table` is called
- **Then** the output SHALL contain one row for every Phase enum member
- **And** rows for phases with no data SHALL display numeric count fields as `0`
- **And** rows for phases with no data SHALL display duration/elapsed fields as `-`

#### Scenario: Table preserves existing data rows unchanged

- **Given** a phase has recorded executions in the metrics data
- **When** `_phase_table` is called
- **Then** that phase's row SHALL display the same count and duration values as before this change
- **And** no existing data SHALL be lost or modified

#### Scenario: Table row order matches Phase enum definition order

- **Given** the Phase enum defines members in a specific order
- **When** `_phase_table` is called
- **Then** the rows in the output table SHALL appear in the same order as the Phase enum members are defined

### Requirement: Phase table MUST NOT depend on data presence for row generation

The `_phase_table` function MUST generate its row list from the Phase enum directly, not from the set of keys present in the aggregated metrics data.

#### Scenario: Empty metrics data produces full table

- **Given** there are no recorded metrics for any phase
- **When** `_phase_table` is called
- **Then** the output SHALL still contain one row per Phase enum member
- **And** every row SHALL show count `0` and duration `-`
