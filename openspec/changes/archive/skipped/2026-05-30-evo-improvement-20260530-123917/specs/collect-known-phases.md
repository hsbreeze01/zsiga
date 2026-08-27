# collect_known_phases

## ADDED Requirements

### Requirement: _collect_known_phases extracts unique phase names

The `_collect_known_phases` function SHALL accept a list of phase-stat dicts and
return a `set[str]` containing every unique key found under each record's
`"phases"` sub-dict. Records that lack a `"phases"` key MUST be tolerated
(treated as having no phases).

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty `set()`

#### Scenario: records without phases key yield nothing

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of records that have no `"phases"` key, e.g. `[{"project_lines": 100}]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be an empty `set()`

#### Scenario: normal extraction with dedup

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records whose `"phases"` dicts share the key `"explore"` and each has a unique key (`"design"`, `"implement"`)
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be `{"explore", "design", "implement"}`
