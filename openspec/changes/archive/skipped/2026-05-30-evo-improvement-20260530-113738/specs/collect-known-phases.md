# collect-known-phases

## ADDED Requirements

### Requirement: _collect_known_phases extracts unique phase names from historical records

The function `_collect_known_phases` SHALL traverse a list of phase stat records and return a set containing every distinct phase name found under the `"phases"` key of each record.

Records missing the `"phases"` key SHALL be treated as having no phases (contributing nothing to the result set). Duplicate phase names across multiple records SHALL be deduplicated in the returned set.

#### Scenario: empty input list returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty set `set()`

#### Scenario: records without phases key contribute nothing

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** records that have no `"phases"` key (e.g. `[{"project_lines": 100}]`)
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty set `set()`

#### Scenario: duplicate phase names across records are deduplicated

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records both containing the same phase name `"explore"` under `"phases"`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL contain exactly one `"explore"` entry

#### Scenario: normal multi-phase extraction

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** records with distinct phase names `"enrich"`, `"implement"`, `"verify"` distributed across multiple records
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be `{"enrich", "implement", "verify"}`
