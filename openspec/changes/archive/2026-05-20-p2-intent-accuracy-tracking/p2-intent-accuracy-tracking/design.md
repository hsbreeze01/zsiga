# Design: P2 Intent Accuracy Tracking + Confidence Gate

## Architecture Decisions

### ADR-1: Record intent in `_process_change()` not `run_cycle()`

**Decision**: Insert the `intent_accuracy` row inside `_process_change()` after
`classify()` returns, not in the `run_cycle()` loop.

**Rationale**: `_process_change()` already has access to `change_name`, `project_name`,
and the full `intent` object. Recording here ensures every classified change gets
tracked regardless of how it enters the pipeline (single-project or cross-project
decomposition).

### ADR-2: Update outcome in the `finally` block of `_process_change()`

**Decision**: Call `update_intent_outcome()` in the `finally` block alongside
`record_change()` and `export_session()`.

**Rationale**: The `finally` block already captures success/reverted outcomes via
`rec.outcome`. For sub-agent dispatches (explore, diagnoser, review), the outcome
is updated immediately after the sub-agent returns. This covers all routing paths
without adding update calls to every branch.

### ADR-3: Confidence gate before routing dispatch

**Decision**: Insert confidence gate logic between `classify()` and the route
dispatch branches in `_process_change()`.

**Rationale**: Placing the gate here means it applies to all change sources uniformly.
The gate only fires for `confidence < 0.6` and non-OPEN_ENDED intents. It dispatches
an explore sub-agent (reusing the existing `_dispatch_explore()` pattern), then
re-classifies with enriched context.

### ADR-4: Reuse existing `intent_tracker.py` functions

**Decision**: Use the existing `record_intent_decision()`, `update_intent_outcome()`,
and `update_intent_reclassification()` from `zsiga.metrics.intent_tracker` directly.

**Rationale**: These functions already have correct SQL, idempotent updates, and
comprehensive test coverage. No need to reimplement.

### ADR-5: Add intent accuracy to `compute_stats()` output

**Decision**: Import `compute_intent_accuracy` from `intent_tracker` and merge its
result into the stats dict under an `intent_accuracy` key.

**Rationale**: The dashboard already reads `compute_stats()` output. Adding a new
key is non-breaking and gives the dashboard access to accuracy data without new
API surface.

## Data Flow

```
_process_change()
  │
  ├─ classify(proposal_text, source="openspec")
  │    → Intent(verbalization, intent_type, confidence, reasoning)
  │
  ├─ record_intent_decision(change_name, project, predicted_intent,
  │                         confidence, classification_source,
  │                         verbalization, reasoning)
  │    → row_id
  │
  ├─ [if confidence < 0.6 AND intent_type != OPEN_ENDED]
  │    ├─ dispatch explore sub-agent → supplementary_context
  │    ├─ re-classify with enriched context → new_intent
  │    ├─ update_intent_reclassification(row_id, old, new)
  │    └─ use new_intent for routing
  │
  ├─ route(intent) → route_path
  │
  ├─ [branch by route_path]
  │    ├─ ask_user → update_intent_outcome("routed", True)
  │    ├─ dispatch_explore → update_intent_outcome(result, is_correct)
  │    ├─ dispatch_diagnoser → update_intent_outcome(result, is_correct)
  │    ├─ dispatch_review → update_intent_outcome(result, is_correct)
  │    └─ pipeline / pipeline_fix → _run_phases(...)
  │
  └─ finally:
       ├─ record_change(rec)
       ├─ update_intent_outcome(change_name, rec.outcome, is_correct)
       └─ export_session(change_name)
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/pipeline/orchestrator.py` | Import intent_tracker functions; add recording after classify(); add confidence gate; add outcome update in finally block and sub-agent branches |
| `zsiga/agent/orchestrator.py` | Same changes as pipeline orchestrator (parallel impl) |
| `zsiga/metrics/collector.py` | Import `compute_intent_accuracy` and add `intent_accuracy` key to `compute_stats()` output |
| `zsiga/metrics/collector.py` | Also add `intent_accuracy` to `_empty_stats()` default |

## Files NOT Modified (already complete)

| File | Status |
|------|--------|
| `zsiga/metrics/db.py` | `intent_accuracy` table already exists in `_SCHEMA` |
| `zsiga/metrics/intent_tracker.py` | All CRUD functions already implemented |
| `tests/test_intent_tracker.py` | Comprehensive tests already exist |
