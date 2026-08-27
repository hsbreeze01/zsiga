# collect-known-phases

## ADDED Requirements

### Requirement: _collect_known_phases extracts unique phase names

The `_collect_known_phases` function SHALL accept a list of phase_stats records
and return a `set[str]` containing every unique phase name found across all records'
`"phases"` dictionaries.

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty `set()`

#### Scenario: single record with multiple phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list with one record whose `"phases"` dict contains keys `"explore"`, `"design"`, `"implement"`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "design", "implement"}`

#### Scenario: multiple records with overlapping phases deduplicates

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records: one with phases `{explore, design}` and another with `{design, implement}`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"explore", "design", "implement"}`
- **And** `"design"` SHALL appear exactly once

#### Scenario: record missing phases key produces empty contribution

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a record with no `"phases"` key
- **When** `_collect_known_phases` processes that record
- **Then** it SHALL not raise an exception
- **And** the record SHALL contribute no phase names to the result set
