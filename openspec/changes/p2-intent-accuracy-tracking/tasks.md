# Tasks: P2 Intent Accuracy Tracking + Confidence Gate

## Group 1: Intent Recording in Pipeline Orchestrator

- [ ] 1.1 Add intent recording to `zsiga/pipeline/orchestrator.py` — import `record_intent_decision`, `update_intent_outcome`, `update_intent_reclassification` from `intent_tracker`; call `record_intent_decision()` after `classify()` in `_process_change()` with all required fields; call `update_intent_outcome()` in the `finally` block mapping `rec.outcome` to `is_correct`; add `update_intent_outcome()` calls in each sub-agent dispatch path (explore, diagnoser, review) and in the `ask_user` path

- [ ] 1.2 Add intent recording to `zsiga/agent/orchestrator.py` — same pattern as 1.1 applied to the parallel orchestrator file

## Group 2: Confidence Gate

- [ ] 2.1 Add confidence gate logic in `zsiga/pipeline/orchestrator.py` — after recording intent decision, check if `confidence < 0.6` and `intent_type != OPEN_ENDED`; if so, dispatch explore sub-agent to gather context, re-classify with enriched proposal text, call `update_intent_reclassification()`, and use the new intent for routing; handle explore failure gracefully (fall back to original classification)

- [ ] 2.2 Add confidence gate logic in `zsiga/agent/orchestrator.py` — same pattern as 2.1

## Group 3: Stats Integration

- [ ] 3.1 Add intent accuracy to `zsiga/metrics/collector.py` — import `compute_intent_accuracy` from `intent_tracker`; in `compute_stats()`, call it and merge result into stats dict under `intent_accuracy` key; add default `intent_accuracy` section to `_empty_stats()`

## Group 4: Tests

- [ ] 4.1 Add integration tests for pipeline orchestrator intent recording — test that `record_intent_decision` is called with correct args after classify, test that `update_intent_outcome` is called on success/revert/sub-agent paths, test confidence gate triggers explore and reclassification, mock sub-agents and verify recording calls

