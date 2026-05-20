# Design: Intent Accuracy Tracking + Confidence Gate

## Architecture Decisions

### 1. New `intent_accuracy` table in existing sqlite3 DB

**Decision**: Add the table to the same `data/zsiga.db` used by all other metrics.

**Rationale**: The existing `zsiga/metrics/db.py` already manages schema creation via `_SCHEMA`.
Adding a new table there follows the established pattern. No new database or storage backend needed.

### 2. New module `zsiga/metrics/intent_tracker.py`

**Decision**: Create a dedicated module for intent accuracy CRUD, rather than bloating `db.py`.

**Rationale**: `db.py` handles generic changes/journal/lessons/snapshots. Intent tracking has its
own domain logic (source detection, accuracy computation, rolling window queries). A separate module
keeps responsibilities clean.

### 3. Classification source detection via keyword analysis

**Decision**: Detect the classification source by checking `Intent.reasoning` and `source` parameter
in the orchestrator, not by modifying the `Intent` dataclass.

**Rationale**: Adding a `source` field to the `Intent` dataclass would be cleaner but requires
touching the intent_router API surface. Instead, the orchestrator (which is the only caller that
records accuracy) detects source from context:
- `source="openspec"` → `classification_source="openspec_override"`
- LLM result was used (check if reasoning contains "LLM=" or is from the LLM path) → `"llm"`
- Otherwise → `"keyword"`

Actually, a cleaner approach: add a `_source` attribute to the returned Intent via a convention in
`classify()`. Since `Intent` is a dataclass, we can check the `reasoning` string — the LLM path
includes "LLM classified" or similar, keyword path includes "关键词". The orchestrator uses
simple substring matching to determine source. **Even cleaner**: add a `source` field to `Intent`
with default `"keyword"`, set to `"llm"` or `"openspec"` by `classify()`. This is a minimal,
backward-compatible change.

**Final decision**: Add `source: str = "keyword"` field to `Intent` dataclass. The `classify()`
function already has all the information; it sets `source` appropriately. No API break since it
has a default value.

### 4. Confidence gate implemented in orchestrator, not intent_router

**Decision**: The confidence gate logic (explore → re-classify) lives in `ZsigaOrchestrator._process_change()`.

**Rationale**: The intent_router is a pure classification function with no side effects. The
confidence gate requires dispatching a sub-agent (I/O operation), which is the orchestrator's job.

### 5. Re-classification uses enriched context

**Decision**: When confidence < 0.6, run `_dispatch_explore()` first, then feed the explore result
back into `classify()` via a new optional `context_hint` parameter.

**Rationale**: Re-classifying with the same input would produce the same result. The explore step
provides new information. The `context_hint` parameter allows passing supplementary context without
changing the core classification API.

## Data Flow

```
_process_change()
  │
  ├─ classify(proposal_text) → Intent + source
  │   └─ record_intent_decision(change_name, project, intent, source)
  │
  ├─ if confidence < 0.6 AND route == "pipeline":
  │   ├─ _dispatch_explore(...) → explore_result
  │   ├─ classify(proposal_text, context_hint=explore_result) → new Intent
  │   └─ update_intent_record(original_row_id, reclassified_intent)
  │
  ├─ route(intent) → execute pipeline / sub-agent
  │
  └─ after _run_phases():
      └─ update_intent_outcome(change_name, actual_outcome, is_correct)
```

## Intent Accuracy Table Schema

```sql
CREATE TABLE IF NOT EXISTS intent_accuracy (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    change_name           TEXT NOT NULL,
    project               TEXT NOT NULL,
    predicted_intent      TEXT NOT NULL,
    confidence            REAL NOT NULL,
    classification_source TEXT NOT NULL DEFAULT 'keyword',
    verbalization         TEXT DEFAULT '',
    reasoning             TEXT DEFAULT '',
    actual_outcome        TEXT DEFAULT '',
    actual_intent         TEXT DEFAULT '',
    is_correct            INTEGER DEFAULT NULL,
    reclassified_from     TEXT DEFAULT '',
    reclassified_to       TEXT DEFAULT '',
    created_at            TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now')),
    updated_at            TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_intent_change ON intent_accuracy(change_name);
CREATE INDEX IF NOT EXISTS idx_intent_predicted ON intent_accuracy(predicted_intent);
CREATE INDEX IF NOT EXISTS idx_intent_source ON intent_accuracy(classification_source);
```

## Files to Create/Modify

### New files
1. `zsiga/metrics/intent_tracker.py` — CRUD + accuracy computation for intent_accuracy table
2. `tests/test_intent_tracker.py` — unit tests for the new module

### Modified files
3. `zsiga/metrics/db.py` — add `intent_accuracy` table to `_SCHEMA` string
4. `zsiga/agent/intent_router.py` — add `source: str = "keyword"` field to `Intent` dataclass;
   set source appropriately in `classify()` return paths
5. `zsiga/pipeline/orchestrator.py` — in `_process_change()`: record intent decision after
   `classify()`, add confidence gate, update outcome after pipeline; import from `intent_tracker`
6. `zsiga/intake/reflector.py` — in `_scan_metric_degradation()`: add intent accuracy checks
7. `zsiga/metrics/collector.py` — in `compute_stats()`: include intent accuracy fields
8. `tests/test_intent_router.py` — update `Intent` construction in tests to account for new `source` field
9. `tests/test_reflector.py` — add tests for intent accuracy signal detection

### Scope: frontend
- None — dashboard updates are out of scope for this change
