# Design: Intent Router OpenSpec Awareness + Construction Marker Semantic Distinction

## Overview

Three fixes to `zsiga/agent/intent_router.py` to prevent misclassification of OpenSpec proposals:

1. **OpenSpec source bypass** — Already implemented: `classify(source="openspec")` returns IMPLEMENTATION directly.
2. **Construction marker detection** — NEW: reduce INVESTIGATION score when proposal describes building a feature.
3. **`_verbalize()` sync** — NEW: skip INVESTIGATION verbalization when construction markers are present.

No changes to `orchestrator.py` (it already passes `source="openspec"`).

## Architecture Decisions

### ADR-1: Source bypass is the primary defense, construction markers are secondary

**Decision:** `source="openspec"` short-circuits at the top of `classify()`, guaranteeing correct routing for daemon-mode proposals. Construction markers protect the keyword fallback path for non-OpenSpec callers.

**Rationale:** In daemon mode, orchestrator always passes `source="openspec"`. Construction markers handle edge cases where `classify()` is called without source (e.g. CLI, tests, future callers).

### ADR-2: Score reduction of 4 points for construction context

**Decision:** When `_CONSTRUCTION_MARKERS` matches alongside `_INVESTIGATION_KEYWORDS`, subtract 4 from the INVESTIGATION score (floor 0).

**Rationale:** The motivating case had 9 investigation matches. Subtracting 4 yields 5, which is still high. But IMPLEMENTATION keywords get +1 base + target bonus (+2), so with even 2–3 impl keywords the score (3 + 1 + 2 = 6) beats the reduced investigation score (5). This calibration handles the "异常诊断面板" case while preserving genuine investigation detection for messages with no construction context.

### ADR-3: `_verbalize()` uses same construction marker pattern

**Decision:** `_verbalize()` imports and checks `_CONSTRUCTION_MARKERS`. When both investigation keywords and construction markers match, the investigation verbalization branch is skipped, falling through to the next keyword match.

**Rationale:** Verbalization drives the `intent.verbalization` field logged by the orchestrator. A wrong verbalization ("排查或调试") even with correct `intent_type` causes confusion in logs and downstream.

## Data Flow

```
classify(message, source="openspec")
  ├─ source == "openspec"? → return IMPLEMENTATION (0.95)  [already done]
  └─ source == None →
       ├─ LLM attempt (if config available)
       └─ Keyword scoring:
            invest_matches → check _CONSTRUCTION_MARKERS
              ├─ has_construction=True → invest_score = max(0, score - 4)
              └─ has_construction=False → invest_score unchanged
            → pick highest score → return Intent
```

```
_verbalize(message)
  ├─ FIX keywords? → "修复..."
  ├─ INVESTIGATION keywords?
  │    ├─ has_construction=True → SKIP (fall through)
  │    └─ has_construction=False → "排查或调试..."
  ├─ IMPL keywords? → "实现或创建..."
  └─ ...
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/agent/intent_router.py` | Add `_CONSTRUCTION_MARKERS` regex; modify keyword scoring in `classify()` to reduce INVESTIGATION score when construction markers present; modify `_verbalize()` to skip INVESTIGATION branch when construction markers present |
| `tests/test_intent_router.py` | Add test cases for construction marker scenarios and updated verbalization |

No other files need modification. `orchestrator.py` already passes `source="openspec"`.
