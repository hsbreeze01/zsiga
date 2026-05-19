# Design: Self-Review Loop Module

## Architecture Decision

The self-review loop is implemented as a dedicated module (`agent/reviewer.py`) that is integrated into the orchestrator pipeline as Phase 2.5, between IMPLEMENT (Phase 2) and VERIFY (Phase 3).

### Key Design Decisions

1. **Separate module, not inline**: `reviewer.py` is a standalone module in `agent/`, not embedded in orchestrator. This allows the review sub-agent to also be dispatched standalone via intent routing (`dispatch_review` path).

2. **Review-role sub-agent**: The review uses `create_with_role("review")` which provides read-only tools and a specialized system prompt. This ensures the reviewer cannot modify code directly.

3. **Fix via main agent, not sub-agent**: When CRITICAL issues are found, the fix is executed by the main `AgentLoop` (not a sub-agent), because fixes require write access and benefit from the agent's full context.

4. **SUGGESTION = CLEAN**: Only CRITICAL issues trigger fixes. SUGGESTION-level issues are informational and do not block the pipeline.

5. **Review does not block pipeline**: Even if review finds ISSUES_FOUND after max rounds, the pipeline continues to VERIFY phase. Review is advisory.

6. **Configurable via pipeline config**: All review parameters (max_rounds, max_turns, timeout, fix_max_turns) are configurable in `zsiga.yaml` under the `pipeline` section. Setting `review_max_rounds: 0` disables review entirely.

## Data Flow

```
IMPLEMENT Phase
       │
       ▼
Mechanical Verification (lint + test)
       │ passed
       ▼
Phase 2.5: REVIEW
       │
       ├─ dispatch review sub-agent (read-only, review role)
       │   input: specs + design + tasks + git diff
       │   output: review.md (Verdict + Issues)
       │
       ├─ parse review.md → (verdict, issues)
       │
       ├─ if CLEAN or SUGGESTION-only → done
       │
       ├─ if CRITICAL:
       │   ├─ main agent fixes (write tools, restricted to changed files)
       │   ├─ re-dispatch review sub-agent
       │   └─ repeat up to max_rounds
       │
       └─ record PhaseRecord(phase=REVIEW, ...)
       │
       ▼
VERIFY Phase
```

## Metrics Integration

- `Phase.REVIEW` already exists in `metrics/types.py`
- Orchestrator already records `PhaseRecord` for review
- **Gap**: `metrics/collector.py` `compute_stats()` only iterates over `["enrich", "implement", "verify", "deliver"]` — needs `"review"` added
- Review stats will show pass rate (CLEAN vs ISSUES_FOUND), average duration, fix attempts

## Prompt Alignment Fix

Current state:
- `agent/reviewer.py` defines `REVIEW_SYSTEM` with `Verdict: CLEAN|ISSUES_FOUND` format — **UNUSED**
- `agent/roles.py` defines `_REVIEW_PROMPT` with `## Verdict: PASS|FAIL` format — **ACTIVELY USED** via `create_with_role("review")`
- `parse_review_verdict()` expects `Verdict: CLEAN|ISSUES_FOUND`

The fix: Update `_REVIEW_PROMPT` in `roles.py` to match the `REVIEW_SYSTEM` format from `reviewer.py`, ensuring system prompt and parser are aligned. Remove the dead `REVIEW_SYSTEM` constant.

## Lesson Recording

After review loop completes with `had_critical=True`, the orchestrator SHALL call `record_lesson()` with a descriptive pattern_key `"pipeline.review.critical"`. This ensures recurring review failures become part of the agent's institutional memory.

## Files to Modify

| File | Change Type | Description |
|------|------------|-------------|
| `zsiga/agent/roles.py` | MODIFIED | Update `_REVIEW_PROMPT` to use `CLEAN\|ISSUES_FOUND` verdict format, align with `parse_review_verdict()` |
| `zsiga/agent/reviewer.py` | MODIFIED | Remove unused `REVIEW_SYSTEM` constant; add review lesson recording helper |
| `zsiga/metrics/collector.py` | MODIFIED | Add `"review"` to phase_stats computation loop |
| `zsiga/pipeline/orchestrator.py` | MODIFIED | Add `record_lesson()` call after review loop when `had_critical=True` |
| `tests/test_reviewer.py` | NEW | Unit tests for `parse_review_verdict`, `ReviewLoopResult`, `_has_critical`, `_build_fix_prompt` |

## Files NOT Modified (already correct)

- `zsiga/metrics/types.py` — `Phase.REVIEW` already exists
- `zsiga/config.py` — `review_*` config fields already exist in `PipelineConfig`
- `zsiga/agent/sub_agent.py` — sub-agent dispatch already works correctly
- `zsiga/pipeline/orchestrator.py` Phase 2.5 integration — already exists and works
