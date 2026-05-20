# Delta Spec: Phase Table Completeness

## MODIFIED Requirements

### Requirement: Phase Performance Table Shows All Enum Values

The `_phase_table` function in `zsiga/metrics/dashboard.py` SHALL emit one table row for every value defined in the Phase enumeration, regardless of whether historical timing data exists for that phase. Phases with no recorded data MUST display zero / empty-sentinel values for all numeric columns.

#### Scenario: Phase with recorded history

- **Given** the Phase enumeration contains values `CLARIFY`, `ENRICH`, `IMPLEMENT`, `REVIEW`, `VERIFY`, `OPTIMIZE`, `REFLECT`, `DELIVER`
- **And** timing records exist for `IMPLEMENT` with `count=5`, `mean=12.3`
- **When** `_phase_table` is called with those timing records
- **Then** the rendered table SHALL contain a row for `IMPLEMENT` showing `count=5` and `mean=12.3`
- **And** the table SHALL also contain rows for every other Phase value

#### Scenario: Phase with no recorded history

- **Given** the Phase enumeration contains `CLARIFY` and no timing records exist for `CLARIFY`
- **When** `_phase_table` is called
- **Then** the rendered table SHALL contain a row for `CLARIFY` with `count=0` and `mean=0` (or equivalent zero-sentinel)

#### Scenario: New phases added to enumeration later

- **Given** a future change adds a new value to the Phase enumeration
- **When** `_phase_table` is called
- **Then** the new phase SHALL appear in the rendered table without any code change to `_phase_table` itself
- **Note** This is a SHOULD constraint — the function SHOULD iterate the enum dynamically rather than hard-code phase names
