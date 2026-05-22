# Spec: Filter Noisy Learnings and Inject into Agent Prompts

## ADDED Requirements

### Requirement: Learnings Write Validation Gate

All learnings write paths — `learn.py::record_lesson()`, `learn.py::record_outcome()`, and `db.py::record_lesson()` — SHALL reject entries that match any of the following noise criteria:

1. The primary text content (jsonl: `takeaway` field; DB: `text` field) is empty or fewer than 10 characters.
2. The `pattern_key` starts with `daemon.cycle_error`.

Rejected entries SHALL NOT be written to `memory/learnings.jsonl` or the `lessons` DB table. Each rejection SHALL be logged at DEBUG level with the skip reason.

#### Scenario: Empty takeaway in record_lesson

- **testable**: true
- **target**: zsiga.memory.learn::record_lesson
- **Given** `record_lesson()` is called with `takeaway=""` or `takeaway="short"` (9 chars)
- **When** the function executes
- **Then** no line SHALL be appended to `memory/learnings.jsonl`
- **And** no row SHALL be inserted into the DB `lessons` table

#### Scenario: daemon.cycle_error pattern_key in record_outcome

- **testable**: true
- **target**: zsiga.memory.learn::record_outcome
- **Given** `record_outcome()` produces a `pattern_key` starting with `daemon.cycle_error`
- **When** the function executes
- **Then** no line SHALL be appended to `memory/learnings.jsonl`

#### Scenario: code.unknown pattern_key in record_outcome

- **testable**: true
- **target**: zsiga.memory.learn::record_outcome
- **Given** `record_outcome()` produces a `pattern_key` starting with `code.unknown`
- **When** the function executes
- **Then** no line SHALL be appended to `memory/learnings.jsonl`

#### Scenario: Valid learning is written normally

- **testable**: true
- **target**: zsiga.memory.learn::record_lesson
- **Given** `record_lesson()` is called with `takeaway="This is a valid lesson with enough characters"` and a non-noisy `pattern_key`
- **When** the function executes
- **Then** a valid JSON line SHALL be appended to `memory/learnings.jsonl`

### Requirement: One-time Learnings Cleanup

The system SHALL provide a function `clean_noisy_learnings(base_path)` that scans and removes noise entries from both `memory/learnings.jsonl` and the DB `lessons` table.

Removal criteria (applied to each existing entry):
- `pattern_key` starts with `daemon.cycle_error`
- `pattern_key` equals `code.unknown`
- Text content is empty or fewer than 10 characters (jsonl: `takeaway`; DB: `text`)

#### Scenario: Remove daemon.cycle_error entries from JSONL

- **testable**: true
- **target**: zsiga.memory.learn::clean_noisy_learnings
- **Given** `memory/learnings.jsonl` contains 2 entries with `pattern_key="daemon.cycle_error"` and 3 valid entries
- **When** `clean_noisy_learnings()` is called
- **Then** the file SHALL contain exactly 3 entries
- **And** none of the remaining entries SHALL have `pattern_key` starting with `daemon.cycle_error`

#### Scenario: Remove code.unknown entries from JSONL

- **testable**: true
- **target**: zsiga.memory.learn::clean_noisy_learnings
- **Given** `memory/learnings.jsonl` contains entries with `pattern_key="code.unknown"`
- **When** `clean_noisy_learnings()` is called
- **Then** no remaining entry SHALL have `pattern_key="code.unknown"`

#### Scenario: Remove empty-text entries from JSONL

- **testable**: true
- **target**: zsiga.memory.learn::clean_noisy_learnings
- **Given** `memory/learnings.jsonl` contains entries with empty or <10-char `takeaway` field
- **When** `clean_noisy_learnings()` is called
- **Then** those entries SHALL be removed

#### Scenario: Remove noisy entries from DB lessons table

- **testable**: true
- **target**: zsiga.memory.learn::clean_noisy_learnings
- **Given** the `lessons` DB table contains rows with `pattern_key` starting with `daemon.cycle_error`
- **When** `clean_noisy_learnings()` is called
- **Then** those rows SHALL be deleted from the DB

#### Scenario: Cleanup is idempotent

- **testable**: true
- **target**: zsiga.memory.learn::clean_noisy_learnings
- **Given** `clean_noisy_learnings()` has already been called once
- **When** it is called a second time
- **Then** no additional entries SHALL be removed (already clean)

### Requirement: Relevant Learnings Search

The system SHALL provide a function `find_relevant_learnings(change_name, max_results)` that returns recent learnings relevant to a given change.

Relevance criteria (entry matches if ANY condition is true):
- The entry's `pattern_key` contains a token extracted from `change_name` (split on `-` and `.`)
- The entry's `pattern_key` starts with `pipeline.fail.`
- The entry's `pattern_key` starts with `pipeline.pass.`

Results SHALL be ordered by recency (most recent first), capped at `max_results`.

#### Scenario: Match by change_name token

- **testable**: true
- **target**: zsiga.memory.learn::find_relevant_learnings
- **Given** learnings.jsonl contains an entry with `pattern_key="pipeline.fail.implement"`
- **And** `change_name="fix-implement-bug"`
- **When** `find_relevant_learnings("fix-implement-bug", 5)` is called
- **Then** the entry SHALL be included in results (token "implement" matches)

#### Scenario: Match pipeline.fail wildcard

- **testable**: true
- **target**: zsiga.memory.learn::find_relevant_learnings
- **Given** learnings.jsonl contains an entry with `pattern_key="pipeline.fail.verify.diagnosed"`
- **And** `change_name="unrelated-change"`
- **When** `find_relevant_learnings("unrelated-change", 5)` is called
- **Then** the entry SHALL be included in results (pipeline.fail.* wildcard match)

#### Scenario: Results capped at max_results

- **testable**: true
- **target**: zsiga.memory.learn::find_relevant_learnings
- **Given** learnings.jsonl contains 10 entries matching `pipeline.fail.*`
- **When** `find_relevant_learnings("any-change", 3)` is called
- **Then** exactly 3 results SHALL be returned

#### Scenario: No matching learnings returns empty list

- **testable**: true
- **target**: zsiga.memory.learn::find_relevant_learnings
- **Given** learnings.jsonl contains only entries with `pattern_key="daemon.cycle_error"` and `pattern_key="code.unknown"`
- **When** `find_relevant_learnings("any-change", 5)` is called
- **Then** an empty list SHALL be returned (noise entries excluded from search)

### Requirement: Learnings Injection into IMPLEMENT Prompt

The IMPLEMENT phase system prompt SHALL include a learnings section when relevant past learnings exist.

The section header SHALL be `## Previous Learnings (avoid repeating mistakes)`.
Each learning SHALL be formatted as `- [{pattern_key}] {takeaway}`.
At most 5 learnings SHALL be injected.
If no relevant learnings exist, no section SHALL be added.

#### Scenario: Learnings section injected when relevant entries exist

- **testable**: true
- **target**: zsiga.pipeline.implementer::_build_learnings_section
- **Given** there are 3 learnings with `pattern_key` starting with `pipeline.fail.`
- **When** the IMPLEMENT phase builds its system prompt
- **Then** the prompt SHALL contain `## Previous Learnings (avoid repeating mistakes)`
- **And** the section SHALL contain exactly 3 formatted learning lines

#### Scenario: No learnings section when no relevant entries

- **testable**: true
- **target**: zsiga.pipeline.implementer::_build_learnings_section
- **Given** there are no relevant learnings for the current change
- **When** the IMPLEMENT phase builds its system prompt
- **Then** the prompt SHALL NOT contain `## Previous Learnings`

#### Scenario: Maximum 5 learnings injected

- **testable**: true
- **target**: zsiga.pipeline.implementer::_build_learnings_section
- **Given** there are 8 relevant learnings
- **When** the learnings section is built
- **Then** at most 5 learning lines SHALL appear in the section

### Requirement: Learnings Injection into ENRICH Prompt

The ENRICH phase system prompt SHALL include a learnings section when relevant past learnings exist.

The section header SHALL be `## Relevant Past Experience`.
Each learning SHALL be formatted as `- [{pattern_key}] {takeaway}`.
At most 3 learnings SHALL be injected.
If no relevant learnings exist, no section SHALL be added.

#### Scenario: Learnings section injected in ENRICH prompt

- **testable**: true
- **target**: zsiga.pipeline.enricher::_build_learnings_section
- **Given** there are 2 learnings relevant to the current change
- **When** the ENRICH phase builds its system prompt
- **Then** the prompt SHALL contain `## Relevant Past Experience`
- **And** the section SHALL contain exactly 2 formatted learning lines

#### Scenario: No learnings section when no relevant entries

- **testable**: true
- **target**: zsiga.pipeline.enricher::_build_learnings_section
- **Given** there are no relevant learnings for the current change
- **When** the ENRICH phase builds its system prompt
- **Then** the prompt SHALL NOT contain `## Relevant Past Experience`

#### Scenario: Maximum 3 learnings injected in ENRICH

- **testable**: true
- **target**: zsiga.pipeline.enricher::_build_learnings_section
- **Given** there are 6 relevant learnings
- **When** the learnings section is built
- **Then** at most 3 learning lines SHALL appear in the section

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
