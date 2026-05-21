# Spec: One-time Learnings Noise Cleanup

## ADDED Requirements

### Requirement: JSONL noise removal

A cleanup function SHALL scan `memory/learnings.jsonl` and remove all records
where the `takeaway` field (or `text` field for legacy entries) is empty or
whitespace-only, or where `pattern_key` equals exactly `daemon.cycle_error` or
`code.unknown`.  The function MUST write the cleaned records back to the same
file and return a summary dict with keys `removed` (int) and `kept` (int).

#### Scenario: Removes empty takeaway records

- **testable**: true
- **target**: zsiga/memory/learn.py::cleanup_learnings_jsonl
- **Given** a JSONL file containing one record with `"takeaway": ""` and one valid record
- **When** `cleanup_learnings_jsonl()` is called with that file path
- **Then** the file contains exactly 1 line (the valid record) and the returned summary has `removed: 1, kept: 1`

#### Scenario: Removes daemon.cycle_error records

- **testable**: true
- **target**: zsiga/memory/learn.py::cleanup_learnings_jsonl
- **Given** a JSONL file containing one record with `"pattern_key": "daemon.cycle_error"` and one valid record
- **When** `cleanup_learnings_jsonl()` is called with that file path
- **Then** the file contains exactly 1 line (the valid record) and the returned summary has `removed: 1, kept: 1`

#### Scenario: Removes code.unknown records

- **testable**: true
- **target**: zsiga/memory/learn.py::cleanup_learnings_jsonl
- **Given** a JSONL file containing one record with `"pattern_key": "code.unknown"` and one valid record
- **When** `cleanup_learnings_jsonl()` is called with that file path
- **Then** the file contains exactly 1 line (the valid record) and the returned summary has `removed: 1, kept: 1`

#### Scenario: Preserves valid records

- **testable**: true
- **target**: zsiga/memory/learn.py::cleanup_learnings_jsonl
- **Given** a JSONL file containing 3 valid records with different non-blacklisted pattern keys
- **When** `cleanup_learnings_jsonl()` is called with that file path
- **Then** the file contains exactly 3 lines and the returned summary has `removed: 0, kept: 3`

### Requirement: DB lessons noise removal

The same cleanup function (or a companion) SHALL delete rows from the DB
`lessons` table where `pattern_key` equals `daemon.cycle_error` or
`code.unknown`, or where `text` is empty.  It MUST return a count of deleted
rows.

#### Scenario: Removes blacklisted DB lessons

- **testable**: true
- **target**: zsiga/metrics/db.py::cleanup_lessons
- **Given** a DB with 2 rows: one with `pattern_key='daemon.cycle_error'` and one with `pattern_key='pipeline.fail.implement'`
- **When** `cleanup_lessons()` is called
- **Then** only 1 row remains (the non-blacklisted one)

#### Scenario: Removes empty-text DB lessons

- **testable**: true
- **target**: zsiga/metrics/db.py::cleanup_lessons
- **Given** a DB with 2 rows: one with `text=''` and one with `text='valid'`
- **When** `cleanup_lessons()` is called
- **Then** only 1 row remains (the one with non-empty text)
