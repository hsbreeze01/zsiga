# Design: Learnings Search

## Architecture Decision

Add `search_learnings()` to the existing `zsiga/memory/learn.py` module. This is the natural home: the module already owns `record_lesson()` and `record_outcome()` which write to `learnings.jsonl`, so the read/search function belongs here too.

## Data Flow

```
caller (active_context, CLI, etc.)
  │
  ▼
search_learnings(keywords, pattern_key=None)
  │
  ├─ read memory/learnings.jsonl
  ├─ parse each JSONL line → dict
  ├─ filter by pattern_key (if provided)
  ├─ for each entry, count unique keyword matches across title/context/takeaway
  ├─ keep entries with score >= 1
  ├─ sort by (-score, -timestamp)
  └─ return list[dict] with _score field
```

## Relevance Scoring

- For each entry, check each keyword (case-insensitive) against `title`, `context`, and `takeaway` fields
- Count the number of **unique** keywords that match at least once
- Score = count of matched unique keywords
- Sort descending by score, then descending by `ts` (most recent first)

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/memory/learn.py` | Add `search_learnings()` function |
| `tests/test_learnings_search.py` | New test file covering all scenarios |

## Implementation Notes

- Follow existing module patterns: use `_MEMORY_DIR` constant already defined in `learn.py`
- Use `json.loads()` per line, same pattern as `pattern_miner.py` and `context.py`
- Return plain `list[dict]` — no new dataclass needed, keeps it lightweight
- `_score` field prefixed with underscore to distinguish from original entry fields
- Gracefully handle missing file, malformed JSON lines (skip them, same as `pattern_miner.py`)
