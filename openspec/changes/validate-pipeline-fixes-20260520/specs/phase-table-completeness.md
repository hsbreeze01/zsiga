# Spec: phase-table-completeness

## MODIFIED Requirements

### Requirement: Phase Performance table SHALL enumerate all Phase enum members

The `_phase_table` function in `zsiga/metrics/dashboard.py` (or equivalent metrics module) SHALL iterate over every member of the `Phase` enumeration and produce one table row per member, regardless of whether historical metric data exists for that phase.

#### Scenario: Phase with no recorded metrics appears as zero-count row

- **Given** the `Phase` enumeration includes at least the members `CLARIFY`, `ENRICH`, `IMPLEMENT`, `REVIEW`, `VERIFY`, `OPTIMIZE`, `REFLECT`, `DELIVER`
- **And** the metrics database contains zero records for the `CLARIFY` phase
- **When** `_phase_table` is invoked
- **Then** the returned table structure SHALL contain a row for `CLARIFY` with count/duration values of `0`
- **And** no `Phase` enum member SHALL be omitted from the output

#### Scenario: Phase with recorded metrics appears with correct data

- **Given** the metrics database contains 3 records for the `IMPLEMENT` phase
- **When** `_phase_table` is invoked
- **Then** the row for `IMPLEMENT` SHALL display count `3`
- **And** all other phases SHALL still appear (with `0` if no data)

#### Scenario: Output ordering matches Phase enum definition order

- **Given** the `Phase` enumeration defines members in a specific order
- **When** `_phase_table` is invoked
- **Then** the rows in the returned table SHALL appear in the same order as the `Phase` enum definition
- **And** this ordering MUST be stable across multiple invocations

### Requirement: Zero-data phase rows MUST NOT be suppressed

The function MUST NOT skip or filter out any phase that has no corresponding metric records. Every member of the `Phase` enum SHALL produce exactly one row.

#### Scenario: Newly added phase enum member is automatically included

- **Given** a new member is added to the `Phase` enumeration in the future
- **When** `_phase_table` is invoked
- **Then** the new member SHALL appear in the output without any code changes to `_phase_table` beyond the enum iteration logic
