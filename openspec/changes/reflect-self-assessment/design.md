# Design: Self-Assessment Phase (REFLECT)

## Architecture Decision

**Insert REFLECT as Phase 3.5 (between VERIFY and DELIVER)** in `_run_phases()` of `pipeline/orchestrator.py`, mirroring how Phase 2.5 (REVIEW) was inserted between IMPLEMENT and VERIFY.

The REFLECT phase is purely computational — no LLM calls, no file modifications to the target project. It computes self-assessment metrics from data already collected during preceding phases.

## Data Flow

```
IMPLEMENT (phases data)
    ↓
REVIEW (phase data)
    ↓
VERIFY (phase data)
    ↓
REFLECT:
  1. Collect PhaseRecords from rec.phases → compute metrics
  2. Derive task_type from intent classification (IMPLEMENTATION→impl, FIX→fix, REFACTOR→refactor)
  3. Compute self_rating from fix_attempts + outcome
  4. Build strengths/weaknesses/lessons arrays (rule-based)
  5. Write reflect.md to change_dir (via transport)
  6. Insert row into self_assessment table (metrics/db.py)
  7. Check capability boundary (3 consecutive poor ratings) → record_lesson if triggered
  8. Append PhaseRecord(phase=REFLECT, outcome=SUCCESS) to rec.phases
    ↓
DELIVER
```

## Self-Rating Algorithm

```
if rec.outcome == REVERTED or total_fix_attempts > 5:
    rating = "poor"
elif total_fix_attempts == 0:
    rating = "excellent"
elif total_fix_attempts <= 2:
    rating = "good"
else:
    rating = "average"
```

## Strengths/Weaknesses Derivation (Rule-Based)

**Strengths** (non-LLM heuristic):
- Zero fix_attempts in IMPLEMENT → "Clean implementation (no mechanical errors)"
- Zero fix_attempts in VERIFY → "First-pass verification"
- First-pass in IMPLEMENT → "Strong code generation accuracy"
- Review verdict was CLEAN → "Clean review (no critical issues)"

**Weaknesses**:
- fix_attempts > 0 in IMPLEMENT → "Required mechanical error fixes"
- fix_attempts > 0 in VERIFY → "Failed initial verification"
- Outcome is REVERTED → "Task exceeded recovery capacity"
- Review had critical issues → "Review found critical issues"

## Capability Boundary Detection

After inserting the self_assessment row, query the last N rows for the same task_type ordered by created_at DESC. If the 3 most recent all have `self_rating = "poor"`, call `record_lesson()` with the boundary pattern key.

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/metrics/types.py` | Add `REFLECT = "reflect"` to `Phase` enum |
| `zsiga/metrics/db.py` | Add `self_assessment` table to `_SCHEMA`; add `record_self_assessment()` and `query_self_assessment_stats()` functions |
| `zsiga/pipeline/orchestrator.py` | Add `phase_reflect()` method; call it in `_run_phases()` after VERIFY success, before DELIVER |
| `tests/test_reflector.py` | (existing, no changes needed — reflector is the intake component, not the REFLECT phase) |

## New Files

| File | Purpose |
|------|---------|
| `tests/test_self_assessment.py` | Tests for self_assessment DB functions, rating algorithm, boundary detection, and reflect.md generation |

## Key Design Decisions

1. **No LLM in REFLECT**: Self-assessment is fully rule-based. This keeps it fast, deterministic, and free of hallucination risk.
2. **reflect.md stored in change_dir**: Consistent with how `verify.md`, `diagnosis.md` are stored — per-change artifacts on the transport layer.
3. **task_type derived from intent**: The `IntentType` already classified at the start of `_process_change()` is passed through to `_run_phases()` → REFLECT.
4. **predicted_tokens/steps default to 0**: CLARIFY-phase token prediction is future scope; the schema supports it but REFLECT just records 0 for now.
5. **Phase enum extension**: Add REFLECT to the existing Phase enum so PhaseRecord can represent it.

## Task Type Mapping

```python
INTENT_TO_TASK_TYPE = {
    IntentType.IMPLEMENTATION: "impl",
    IntentType.FIX: "fix",
    # Default fallback for other intents that reach pipeline:
    # "refactor" (not a current IntentType, but extensible)
}
```
