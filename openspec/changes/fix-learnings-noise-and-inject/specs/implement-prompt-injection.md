# Spec: IMPLEMENT Prompt Learnings Injection

## MODIFIED Requirements

### Requirement: Learnings section in implementer system prompt

The `implement` function in `zsiga/pipeline/implementer.py` SHALL append a
learnings section to the `system_prompt` when relevant learnings exist.  The
section MUST use the header `## Previous Learnings (avoid repeating mistakes)`
and contain up to 5 formatted learning entries.  When no relevant learnings
exist, the section SHALL NOT be added (no empty section header).

#### Scenario: System prompt includes learnings section when learnings exist

- **testable**: true
- **target**: zsiga/pipeline/implementer.py::implement
- **Given** `memory/learnings.jsonl` contains entries with `pattern_key="pipeline.fail.implement"` and non-empty takeaway
- **When** the `implement` function builds its system prompt
- **Then** the resulting system prompt string contains the literal text `## Previous Learnings (avoid repeating mistakes)`

#### Scenario: System prompt omits learnings section when no learnings match

- **testable**: true
- **target**: zsiga/pipeline/implementer.py::implement
- **Given** `memory/learnings.jsonl` is empty
- **When** the `implement` function builds its system prompt
- **Then** the resulting system prompt string does NOT contain `## Previous Learnings`

#### Scenario: Learnings section contains at most 5 entries

- **testable**: true
- **target**: zsiga/pipeline/implementer.py::implement
- **Given** `memory/learnings.jsonl` contains 10 entries with `pattern_key="pipeline.fail.implement"` and valid takeaways
- **When** the `implement` function builds its system prompt
- **Then** the learnings section contains at most 5 lines starting with `- [`

#### Scenario: Each learning entry is formatted as bullet with pattern key

- **testable**: true
- **target**: zsiga/pipeline/implementer.py::implement
- **Given** `memory/learnings.jsonl` contains an entry with `pattern_key="pipeline.fail.implement"` and `takeaway="Never use bare except"`
- **When** the `implement` function builds its system prompt
- **Then** the system prompt contains a line matching `- [pipeline.fail.implement] Never use bare except`
