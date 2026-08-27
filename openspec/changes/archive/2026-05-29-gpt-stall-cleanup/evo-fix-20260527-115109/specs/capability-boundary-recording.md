# capability-boundary-recording

## ADDED Requirements

### Requirement: Capability boundary learning entries

When recording a capability boundary (a non-repairable root cause identified during failure
analysis), the learning entry SHALL contain structured fields: `pattern_key`, `root_cause`,
and `prevention`.

#### Scenario: Capability boundary entry has required fields

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** the learnings.jsonl file exists (or can be created)
- **When** `record_lesson` is called with `title="capability boundary test"`, `context="test"`, `takeaway="test boundary"`, `pattern_key="test.boundary"`, `source="manual"`
- **Then** the last line of learnings.jsonl SHALL be valid JSON containing keys `"pattern_key"`, `"takeaway"`, and `"ts"`

#### Scenario: Existing learnings entries are valid JSON

- **testable**: true
- **target**: memory/learnings.jsonl
- **Given** the file `memory/learnings.jsonl` exists
- **When** each line is parsed
- **Then** every non-empty line SHALL be valid JSON containing at minimum `"type"` and `"ts"` keys
