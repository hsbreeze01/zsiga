# Design: l5-intent-gate — Phase 0 Intent Gate

## Architecture Decision

### Decision 1: Upgrade IntentType enum from 4 → 6 categories

**Current state:** `IntentType` has 4 values: `TRIVIAL`, `EXPLORATION`, `IMPLEMENTATION`, `AMBIGUOUS`.

**New state:** `IntentType` will have 6 values: `RESEARCH`, `IMPLEMENTATION`, `INVESTIGATION`, `EVALUATION`, `FIX`, `OPEN_ENDED`.

**Rationale:** The original 4 categories collapse distinct user intents (debug vs review vs research) into one `EXPLORATION` bucket, losing critical routing information. The new 6 categories map directly to existing Role types (`explore`, `diagnoser`, `review`) plus pipeline variants.

### Decision 2: Add verbalization step before classification

The `classify()` function will first produce a one-sentence verbalization of the user's intent, then use that verbalization (plus raw keywords) for classification. This is a pure rule-based approach — no LLM call — keeping it fast and deterministic.

### Decision 3: Keep rule-based classification (no LLM)

The existing keyword-matching approach works well. We extend the keyword patterns to cover the new categories. No LLM call needed for classification — this keeps Phase 0 fast and deterministic.

### Decision 4: New route target `pipeline_fix`

The `FIX` intent routes to a shortened pipeline that skips ENRICH and goes directly to IMPLEMENT → VERIFY. This is implemented as a new branch in `_process_change()`.

## Data Flow

```
User Message
    │
    ▼
┌──────────────────────┐
│  Verbalize (1-liner) │  ← new: _verbalize()
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Classify (6 types)  │  ← modified: classify()
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Route               │  ← modified: route()
│  ┌─────────────────┐ │
│  │ research → explore       │
│  │ implementation → pipeline│
│  │ investigation → diagnose │
│  │ evaluation → review      │
│  │ fix → pipeline_fix       │
│  │ open-ended → ask_user    │
│  └─────────────────┘ │
└──────────┬───────────┘
           │
           ▼
  Execution Path
```

## Files to Modify

| File | Change |
|---|---|
| `zsiga/agent/intent_router.py` | Major rewrite: new `IntentType` enum (6 values), new `_verbalize()` function, extended keyword patterns, updated `classify()` and `route()` |
| `zsiga/pipeline/orchestrator.py` | Updated `_process_change()`: handle new route targets (dispatch explore/diagnoser/review sub-agents, pipeline_fix path) |
| `tests/test_intent_router.py` | New test file covering all 6 intent categories, verbalization, edge cases |

## Files to Add

| File | Purpose |
|---|---|
| `tests/test_intent_router.py` | Unit tests for the upgraded intent gate |

## Backward Compatibility

- The `Intent` dataclass gains a new field `verbalization` (with default `""`), so existing callers won't break.
- The `IntentType` enum is fully replaced — all callers that import `IntentType` (only `orchestrator.py`) will be updated in the same change.
- The `route()` function signature remains the same (`Intent → str`), only the routing map values change.
