# Spec: Learning Format Upgrade Test Coverage

## ADDED Requirements

### Requirement: record_lesson SHALL persist case/why/rule fields

`record_lesson()` in `learn.py` SHALL accept optional `case` (dict), `why` (str),
and `rule` (str) keyword arguments. When provided, these fields SHALL be written
as top-level keys in the JSON line appended to `learnings.jsonl`.

#### Scenario: record_lesson with case why and rule arguments

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** a fresh learnings.jsonl path (via tmp_path or monkeypatch)
- **When** `record_lesson(title="test", context="ctx", takeaway="tw", case={"what": "something"}, why="because", rule="do X")` is called
- **Then** the last line of learnings.jsonl contains JSON with keys `"case"`, `"why"`, and `"rule"` with the provided values

---

### Requirement: record_outcome SHALL persist case/why/rule fields

`record_outcome()` in `learn.py` SHALL accept optional `case` (dict), `why` (str),
and `rule` (str) keyword arguments. When provided and the outcome is a failure
(`success=False`), these fields SHALL appear in the written lesson record.

#### Scenario: record_outcome with case why and rule arguments

- **testable**: true
- **target**: zsiga/memory/learn.py::record_outcome
- **Given** a fresh learnings.jsonl path (via tmp_path or monkeypatch)
- **When** `record_outcome("change", "proj", False, "verify", case={"what": "w"}, why="y", rule="r")` is called
- **Then** the last line of learnings.jsonl contains JSON with keys `"case"`, `"why"`, and `"rule"`

---

### Requirement: load_recent_lessons SHALL format rule entries with RULE prefix

`load_recent_lessons()` in `context.py` SHALL read learnings.jsonl entries and format
them as strings. Entries containing a `"rule"` field SHALL be prefixed with `[RULE]`.
Entries without a `"rule"` field but with a `"pattern_key"` SHALL be prefixed with
`[pattern_key]`.

#### Scenario: Entries with rule field get RULE prefix

- **testable**: true
- **target**: zsiga/memory/context.py::load_recent_lessons
- **Given** a learnings.jsonl containing two entries: one with `"rule": "do X"` and one with `"pattern_key": "test.key"` but no rule
- **When** `load_recent_lessons()` is called
- **Then** the entry with rule starts with `[RULE]` and the entry with pattern_key starts with `[test.key]`
