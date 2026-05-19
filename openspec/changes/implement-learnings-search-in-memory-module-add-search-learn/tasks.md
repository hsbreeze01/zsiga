# Tasks: Learnings Search

## 1. Core Implementation

- [x] Add `search_learnings(keywords: list[str], pattern_key: str | None = None) -> list[dict]` to `zsiga/memory/learn.py` with keyword matching, pattern_key filtering, relevance scoring, and case-insensitive search

## 2. Test Coverage

- [x] Create `tests/test_learnings_search.py` with tests for: basic keyword match, no-match empty result, missing file graceful handling, pattern_key filtering, combined keyword+pattern_key, relevance ranking by score then recency, case-insensitive matching, result format includes `_score`
