# Spec: ENRICH Prompt Learnings Injection

## MODIFIED Requirements

### Requirement: Learnings section in enricher system prompt

The `enrich` function in `zsiga/pipeline/enricher.py` SHALL append a learnings
section to the `system_prompt` (or user prompt) when relevant learnings exist.
The section MUST use the header `## Relevant Past Experience` and contain up to
3 formatted learning entries.  When no relevant learnings exist, the section
SHALL NOT be added.

#### Scenario: System prompt includes learnings section when learnings exist

- **testable**: true
- **target**: zsiga/pipeline/enricher.py::enrich
- **Given** `memory/learnings.jsonl` contains entries with `pattern_key="pipeline.fail.implement"` and non-empty takeaway
- **When** the `enrich` function builds its prompt
- **Then** the resulting prompt string contains the literal text `## Relevant Past Experience`

#### Scenario: Prompt omits learnings section when no learnings match

- **testable**: true
- **target**: zsiga/pipeline/enricher.py::enrich
- **Given** `memory/learnings.jsonl` is empty
- **When** the `enrich` function builds its prompt
- **Then** the resulting prompt string does NOT contain `## Relevant Past Experience`

#### Scenario: Learnings section contains at most 3 entries

- **testable**: true
- **target**: zsiga/pipeline/enricher.py::enrich
- **Given** `memory/learnings.jsonl` contains 10 entries with `pattern_key="pipeline.fail.implement"` and valid takeaways
- **When** the `enrich` function builds its prompt
- **Then** the learnings section contains at most 3 lines starting with `- [`

#### Scenario: Each learning entry is formatted as bullet with pattern key

- **testable**: true
- **target**: zsiga/pipeline/enricher.py::enrich
- **Given** `memory/learnings.jsonl` contains an entry with `pattern_key="pipeline.pass.deliver"` and `takeaway="Success"`
- **When** the `enrich` function builds its prompt
- **Then** the prompt contains a line matching `- [pipeline.pass.deliver] Success`
