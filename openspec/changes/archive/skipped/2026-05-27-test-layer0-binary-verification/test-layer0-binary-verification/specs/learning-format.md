# Learning Format and Context Tests

## ADDED Requirements

### Requirement: record_lesson with case/why/rule fields
`record_lesson` SHALL accept optional `case`, `why`, and `rule` keyword arguments. When provided, these fields SHALL be persisted as top-level keys in the learnings.jsonl entry.

#### Scenario: record_lesson persists case why and rule

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** a clean temporary learnings.jsonl path (via tmp_path monkeypatch)
- **When** `record_lesson(title="test", context="ctx", takeaway="tw", case={"what": "something"}, why="because", rule="do X")` is called
- **Then** the last line of learnings.jsonl contains a JSON object with keys `"case"`, `"why"`, and `"rule"` with the provided values

---

### Requirement: record_outcome with case/why/rule fields
`record_outcome` SHALL accept optional `case`, `why`, and `rule` keyword arguments for failed outcomes. When provided, these fields SHALL be persisted as top-level keys in the learnings.jsonl entry.

#### Scenario: record_outcome persists case why and rule on failure

- **testable**: true
- **target**: zsiga/memory/learn.py::record_outcome
- **Given** a clean temporary learnings.jsonl path (via tmp_path monkeypatch)
- **When** `record_outcome("change-x", "proj", False, "verify", case={"what": "w"}, why="y", rule="r")` is called
- **Then** the last line of learnings.jsonl contains a JSON object with keys `"case"`, `"why"`, and `"rule"` with the provided values

---

### Requirement: load_recent_lessons prefers [RULE] entries
`load_recent_lessons` SHALL format entries differently based on whether they have a `rule` field. Entries with `rule` SHALL be prefixed with `[RULE]`. Entries without `rule` but with `pattern_key` SHALL be prefixed with `[pattern_key]`. Entries with neither SHALL use the takeaway as-is.

#### Scenario: load_recent_lessons formats RULE entries with priority

- **testable**: true
- **target**: zsiga/memory/context.py::load_recent_lessons
- **Given** a temporary learnings.jsonl containing two entries: one with `"rule": "do X"` and one with only `"pattern_key": "code.lint"` and `"takeaway": "fix lint"`
- **When** `load_recent_lessons()` is called
- **Then** the entry with `rule` starts with `[RULE]` and the entry without `rule` starts with `[code.lint]`
