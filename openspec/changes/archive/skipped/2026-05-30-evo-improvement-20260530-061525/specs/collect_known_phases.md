# collect_known_phases

## ADDED Requirements

### Requirement: _collect_known_phases extracts unique phase names

`_collect_known_phases` SHALL iterate over all records in `phase_stats` and return a `set[str]` of every distinct phase name found in each record's `"phases"` dictionary key set. Records that lack a `"phases"` key SHALL be treated as having an empty phase dictionary.

#### Scenario: empty_input_returns_empty_set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty `phase_stats` list `[]`
- **When** `_collect_known_phases` is called
- **Then** it SHALL return an empty set `set()`

#### Scenario: single_record_with_phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` containing one record `{"phases": {"enrich": 10.0, "implement": 20.0}}`
- **When** `_collect_known_phases` is called
- **Then** it SHALL return `{"enrich", "implement"}`

#### Scenario: multiple_records_with_overlapping_phases

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` containing three records with overlapping phase sets:
  - `{"phases": {"enrich": 5.0, "implement": 10.0}}`
  - `{"phases": {"implement": 12.0, "verify": 8.0}}`
  - `{"phases": {"deliver": 3.0}}`
- **When** `_collect_known_phases` is called
- **Then** it SHALL return `{"enrich", "implement", "verify", "deliver"}`

#### Scenario: record_missing_phases_key

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats` containing one record without a `"phases"` key: `{"project_lines": 100}`
- **When** `_collect_known_phases` is called
- **Then** it SHALL return an empty set `set()`
