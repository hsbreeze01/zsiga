# Spec: phase-table-all-phases

## ADDED Requirements

### Requirement: _phase_table SHALL render every Phase enum member

The `_phase_table` function in `zsiga/metrics/dashboard.py` SHALL iterate over
**all** values of the `Phase` enum and produce a table row for each one.
When no metrics data exists for a given phase, the row SHALL display zero-valued
entries rather than being omitted.

#### Scenario: all phases appear when metrics exist only for a subset

- **Given** the Phase enum contains at least the members
  `CLARIFY`, `ENRICH`, `IMPLEMENT`, `REVIEW`, `VERIFY`, `OPTIMIZE`, `REFLECT`,
  `DELIVER`
- **And** metrics data exists only for `IMPLEMENT` and `REVIEW`
- **When** `_phase_table` is called
- **Then** the resulting HTML table SHALL contain one row for every Phase member
- **And** rows for phases without data SHALL display `0` for count / duration
  columns
- **And** rows for `IMPLEMENT` and `REVIEW` SHALL display their actual metric
  values

#### Scenario: no metrics data at all

- **Given** no phase metrics data exists
- **When** `_phase_table` is called
- **Then** the resulting HTML table SHALL contain one row for every Phase member
- **And** every row SHALL display `0` for all numeric columns

### Requirement: _phase_table MUST preserve existing column layout

The function MUST NOT change the number, order, or heading text of table
columns that already exist in the output.  Only the set of rows is affected.

#### Scenario: column headers unchanged

- **Given** the current `_phase_table` output column headers
- **When** the function is modified to include all phases
- **Then** the column headers and their order SHALL be identical to before the
  change
