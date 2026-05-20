# Design: Fix Review Phase Zero LLM Calls

## Root Cause Analysis

The dashboard reports review phase as having **0 LLM calls, 0 tool calls, 0 prompt tokens** across 28 runs. The root cause is a **metrics recording gap**, not the sub-agent failing to start.

### Bug 1: `ReviewLoopResult` doesn't carry metrics

The `ReviewLoopResult` dataclass in `agent/reviewer.py` only has:
- `final_verdict`, `rounds_executed`, `fix_attempts`, `elapsed_seconds`,
  `last_issues`, `had_critical`

It lacks `llm_calls`, `tool_calls`, `prompt_tokens`, `completion_tokens`.

### Bug 2: `run_review_loop` discards sub-agent results

In `run_review_loop()`:
```python
await run_review(agent, change_dir, ...)  # SubAgentResult discarded!
```
The `SubAgentResult` from `run_review()` is not captured. The LLM call counts
are lost.

Similarly, the fix attempt result is discarded:
```python
await agent.run(system_prompt, user_prompt, max_turns=fix_max_turns)
# RunResult discarded!
```

### Bug 3: Review PhaseRecord has no metrics

In `pipeline/orchestrator.py`, the review PhaseRecord:
```python
rec.phases.append(PhaseRecord(
    phase=Phase.REVIEW, outcome=review_outcome,
    seconds_used=review_seconds,
    fix_attempts=review_result.fix_attempts,
    detail=_summarize_issues(review_result.last_issues),
    # ← missing: llm_calls, tool_calls, prompt_tokens, completion_tokens
))
```

Compare with implement PhaseRecord which correctly includes all metrics.

### Why the dashboard shows 0

`PhaseRecord` defaults `llm_calls=0`, `tool_calls=0`, `prompt_tokens=0`,
`completion_tokens=0`. The `compute_stats()` function in `metrics/collector.py`
reads these from the serialized records. Since review never sets them, they
remain 0.

The `avg_seconds: 99.1` and `pass_rate: 0.0` are real values (the review loop
does execute and often returns non-CLEAN verdicts), but the LLM activity
metrics are all zeros.

## Fix Strategy

1. **Add metrics fields to `ReviewLoopResult`** — `llm_calls`, `tool_calls`,
   `prompt_tokens`, `completion_tokens`.

2. **Capture and accumulate metrics in `run_review_loop`** — Store the
   `SubAgentResult` from `run_review()` and the `RunResult` from `agent.run()`
   fix attempts, summing their metrics.

3. **Wire metrics into orchestrator PhaseRecord** — Pass the accumulated
   metrics from `ReviewLoopResult` into the review `PhaseRecord`.

## Data Flow (After Fix)

```
run_review() → SubAgentResult (llm_calls=6, tool_calls=10, ...)
                    ↓ captured
run_review_loop() → accumulates into ReviewLoopResult
                    ↓ (plus fix RunResult if CRITICAL)
orchestrator._run_phases() → reads ReviewLoopResult metrics
                    ↓
PhaseRecord(llm_calls=12, tool_calls=20, prompt_tokens=..., ...)
                    ↓
metrics/collector.compute_stats() → dashboard shows real numbers
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/agent/reviewer.py` | Add metrics fields to `ReviewLoopResult`; capture `SubAgentResult` from `run_review()` and `RunResult` from fix `agent.run()` in `run_review_loop()` |
| `zsiga/pipeline/orchestrator.py` | Pass `ReviewLoopResult` metrics into review `PhaseRecord` |
| `tests/test_reviewer.py` | Update `TestReviewLoopResult` tests for new fields; add test for metrics accumulation |

## Files NOT Changed

- `zsiga/agent/sub_agent.py` — no changes needed (already returns metrics)
- `zsiga/agent/loop.py` — no changes needed (already tracks metrics)
- `zsiga/metrics/collector.py` — no changes needed (already reads from PhaseRecord)
- Other pipeline phases — scope limited to review
