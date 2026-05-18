# Design: Proposal Deduplication Checker

## Architecture Decision

Create a new module `zsiga/pipeline/dedup.py` containing the deduplication checker logic. This follows the existing pipeline module pattern (e.g., `dependency.py`, `diagnoser.py`) — a self-contained module with dataclasses at the top and pure functions for the public API.

No LLM calls are needed; all logic is deterministic text comparison. No external ML/NLP dependencies are required — similarity is computed via word-level Jaccard index on normalized text.

## Data Models

```python
@dataclass
class ArchivedProposal:
    id: str                     # archived change directory name
    proposal_text: str          # raw proposal.md content

@dataclass
class DuplicateMatch:
    change_id: str              # archived change directory name
    score: float                # similarity score [0.0, 1.0]
    proposal_text: str          # the matched archived proposal text (for context)
```

## Data Flow

```
archive_dir/
  └─ load_archived_proposals() ─→ list[ArchivedProposal]
                │
new_proposal_text ─┐
                   │
        normalize() ─→ cleaned text
                   │
        compute_similarity() ─→ float [0.0, 1.0]  (Jaccard on word sets)
                   │
        check_duplicates() ─→ list[DuplicateMatch]
```

1. **load_archived_proposals**: Lists subdirectories of `archive_dir`, reads each `proposal.md`, returns `list[ArchivedProposal]`. Skips dirs without `proposal.md`.
2. **normalize**: Lowercases, collapses whitespace, strips `# Proposal:` header prefix, removes non-alphanumeric characters except spaces.
3. **compute_similarity**: Tokenizes both normalized texts into word sets, computes Jaccard index = `|intersection| / |union|`.
4. **check_duplicates**: Orchestrates the above — loads archive, computes similarity against each archived proposal, filters by threshold (default 0.5), returns sorted by score descending.

## Similarity Algorithm: Jaccard on Word Sets

```
normalized_a = normalize(text_a)
normalized_b = normalize(text_b)
words_a = set(normalized_a.split())
words_b = set(normalized_b.split())
jaccard = len(words_a & words_b) / len(words_a | words_b)  # 0.0 if both empty
```

This is:
- Fast: O(n) where n = word count
- Deterministic: no randomness
- No external dependencies
- Good enough for detecting near-duplicate proposals (same keywords, reordered)

## Files to Add/Modify

- `zsiga/pipeline/dedup.py` — New module: dataclasses + `load_archived_proposals`, `normalize`, `compute_similarity`, `check_duplicates`
- `tests/test_dedup.py` — New test file covering all PDC-01 through PDC-05 scenarios

## Integration Points

- The orchestrator may optionally call `check_duplicates` before the ENRICH phase to warn about potential duplicates, but that integration is **out of scope** for this change.
- Uses `zsiga.pipeline.utils.read_file` and `zsiga.transport.Transport` for file I/O (following existing patterns in `dependency.py`).
- The `check_duplicates` function accepts an optional `Transport` parameter, consistent with other pipeline modules.

## Key Design Choices

1. **Jaccard word-overlap**: Simple, fast, deterministic, no external deps. Adequate for detecting proposals that are substantially the same.
2. **Transport-agnostic**: Accepts optional `Transport` parameter, same as all pipeline modules.
3. **Dataclass return types**: Following the `dependency.py` pattern with structured results.
4. **Configurable threshold**: Default 0.5, callers can tighten or loosen.
5. **Pure functions**: `normalize` and `compute_similarity` are pure functions, easy to test independently.
