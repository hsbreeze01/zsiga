# Spec: Learnings Inject Utility

## ADDED Requirements

### Requirement: Fetch relevant learnings for prompt injection

A function `fetch_relevant_learnings` SHALL read `memory/learnings.jsonl`,
filter entries by relevance to the given change context, and return the most
recent N entries as formatted markdown text.  Relevance is determined by:

1. **Direct match**: the entry's `pattern_key` contains a keyword from the
   `change_name` (after splitting on `-`/`_`).
2. **Pipeline category match**: the entry's `pattern_key` starts with
   `pipeline.fail.` or `pipeline.pass.` (universal lessons).

Entries matching either rule are included, sorted by `ts` descending, and
truncated to the requested `max_count`.  Each entry is formatted as:
`- [{pattern_key}] {takeaway}`

If no entries match, the function SHALL return an empty string (`""`).

#### Scenario: Returns matching pipeline lessons

- **testable**: true
- **target**: zsiga/memory/learn.py::fetch_relevant_learnings
- **Given** a JSONL file with entries having `pattern_key="pipeline.fail.implement"` and `pattern_key="pipeline.pass.deliver"`
- **When** `fetch_relevant_learnings("fix-foo-bar", max_count=5)` is called
- **Then** the returned string contains `pipeline.fail.implement` and `pipeline.pass.deliver` entries

#### Scenario: Returns direct name match lessons

- **testable**: true
- **target**: zsiga/memory/learn.py::fetch_relevant_learnings
- **Given** a JSONL file with an entry having `pattern_key="code.unknown"` and `takeaway="fix the unknown"`
- **When** `fetch_relevant_learnings("code-unknown-fix", max_count=5)` is called
- **Then** the returned string contains `fix the unknown` (matched via keyword `code` or `unknown`)

#### Scenario: Respects max_count limit

- **testable**: true
- **target**: zsiga/memory/learn.py::fetch_relevant_learnings
- **Given** a JSONL file with 10 entries having `pattern_key="pipeline.fail.implement"`
- **When** `fetch_relevant_learnings("any-change", max_count=3)` is called
- **Then** the returned string contains exactly 3 bullet points (lines starting with `- [`)

#### Scenario: Returns empty string when no matches

- **testable**: true
- **target**: zsiga/memory/learn.py::fetch_relevant_learnings
- **Given** a JSONL file with entries having `pattern_key="ops.service_management"`
- **When** `fetch_relevant_learnings("fix-xyz", max_count=5)` is called
- **Then** the returned string is `""` (no pipeline or name-match keywords hit)

#### Scenario: Skips entries with missing takeaway

- **testable**: true
- **target**: zsiga/memory/learn.py::fetch_relevant_learnings
- **Given** a JSONL file with an entry having `pattern_key="pipeline.fail.implement"` and `"takeaway": ""`
- **When** `fetch_relevant_learnings("any-change", max_count=5)` is called
- **Then** that entry is not included in the output (no bullet for empty takeaway)
