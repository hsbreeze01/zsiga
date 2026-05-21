# Spec: Learnings Write Validation

## ADDED Requirements

### Requirement: Text length gate on learnings write

All code paths that append entries to `memory/learnings.jsonl` (including
`record_lesson`, `record_outcome`, and `record_success` in `zsiga.memory.learn`)
MUST skip writing when the primary text field (`takeaway` for lessons, `title`
for success patterns) is empty or shorter than 10 characters.

Skipped entries SHALL be counted and logged at DEBUG level with a message
containing the pattern key and the reason (`text_too_short` or
`pattern_blacklisted`).

#### Scenario: Empty takeaway is rejected

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** `memory/learnings.jsonl` exists with N lines
- **When** `record_lesson(title="x", context="y", takeaway="", pattern_key="test.pk")` is called
- **Then** the file still has exactly N lines (no new entry written)

#### Scenario: Short takeaway is rejected

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** `memory/learnings.jsonl` exists with N lines
- **When** `record_lesson(title="x", context="y", takeaway="short", pattern_key="test.pk")` is called (takeaway = 5 chars < 10)
- **Then** the file still has exactly N lines

#### Scenario: Valid takeaway is written

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** `memory/learnings.jsonl` exists with N lines
- **When** `record_lesson(title="x", context="y", takeaway="this is a valid takeaway text", pattern_key="test.pk")` is called
- **Then** the file has N+1 lines and the last line is valid JSON containing `"takeaway": "this is a valid takeaway text"`

### Requirement: Pattern key blacklist gate

All code paths that append entries to `memory/learnings.jsonl` MUST skip writing
when the `pattern_key` starts with any entry in a configurable blacklist.  The
default blacklist SHALL contain at minimum `daemon.cycle_error`.

#### Scenario: daemon.cycle_error pattern is rejected

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** `memory/learnings.jsonl` exists with N lines
- **When** `record_lesson(title="x", context="y", takeaway="a sufficiently long takeaway message", pattern_key="daemon.cycle_error")` is called
- **Then** the file still has exactly N lines

#### Scenario: daemon.cycle_error prefix pattern is rejected

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** `memory/learnings.jsonl` exists with N lines
- **When** `record_lesson(title="x", context="y", takeaway="a sufficiently long takeaway message", pattern_key="daemon.cycle_error.git_checkout")` is called
- **Then** the file still has exactly N lines

#### Scenario: Non-blacklisted pattern with valid text is written

- **testable**: true
- **target**: zsiga/memory/learn.py::record_lesson
- **Given** `memory/learnings.jsonl` exists with N lines
- **When** `record_lesson(title="x", context="y", takeaway="a sufficiently long takeaway", pattern_key="pipeline.fail.implement")` is called
- **Then** the file has N+1 lines

### Requirement: DB lessons write validation

The `record_lesson` function in `zsiga/metrics/db.py` MUST apply the same text
length and pattern key blacklist validation before inserting into the `lessons`
table.  Rows that fail validation SHALL NOT be inserted.

#### Scenario: DB record_lesson rejects blacklisted pattern

- **testable**: true
- **target**: zsiga/metrics/db.py::record_lesson
- **Given** a clean test DB with 0 lessons rows
- **When** `db.record_lesson(text="some text", pattern_key="daemon.cycle_error")` is called
- **Then** `db.count_lessons()` returns 0

#### Scenario: DB record_lesson accepts valid entry

- **testable**: true
- **target**: zsiga/metrics/db.py::record_lesson
- **Given** a clean test DB with 0 lessons rows
- **When** `db.record_lesson(text="valid lesson text here", pattern_key="pipeline.fail.implement")` is called
- **Then** `db.count_lessons()` returns 1

#### Scenario: DB record_lesson rejects empty text

- **testable**: true
- **target**: zsiga/metrics/db.py::record_lesson
- **Given** a clean test DB with 0 lessons rows
- **When** `db.record_lesson(text="", pattern_key="pipeline.fail.implement")` is called
- **Then** `db.count_lessons()` returns 0
