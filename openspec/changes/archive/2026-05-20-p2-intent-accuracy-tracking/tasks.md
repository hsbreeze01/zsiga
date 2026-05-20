# Tasks: Intent Accuracy Tracking + Confidence Gate

## Group 1: Data Layer

- [x] 1.1 Add `intent_accuracy` table schema and index to `zsiga/metrics/db.py` `_SCHEMA` string
- [x] 1.2 Create `zsiga/metrics/intent_tracker.py` with `record_intent_decision()`, `update_intent_outcome()`, `update_intent_reclassification()`, and `compute_intent_accuracy()` functions
- [x] 1.3 Create `tests/test_intent_tracker.py` covering record, update, accuracy computation, rolling window, and edge cases (empty table, missing row)

## Group 2: Intent Source Tracking

- [ ] 2.1 Add `source: str = "keyword"` field to `Intent` dataclass in `zsiga/agent/intent_router.py`; set `source="llm"` in LLM return paths, `source="openspec"` in openspec override, `source="keyword"` in keyword fallback paths
- [ ] 2.2 Update all `Intent(...)` constructor calls in `tests/test_intent_router.py` to include `source` field (or rely on default); verify existing tests pass with `ruff` and `pytest`

## Group 3: Orchestrator Integration

- [ ] 3.1 In `zsiga/pipeline/orchestrator.py` `_process_change()`: after `classify()`, call `record_intent_decision()` from intent_tracker; after `_run_phases()` completes (success or failure), call `update_intent_outcome()` with actual outcome and `is_correct` (True for SUCCESS/DELIVER, False for REVERTED/FAIL)
- [ ] 3.2 In `zsiga/pipeline/orchestrator.py` `_process_change()`: add confidence gate — if `intent.confidence < 0.6` and `route_path == "pipeline"`, dispatch explore sub-agent, then re-classify with `context_hint`, and call `update_intent_reclassification()` on the original record; update `route_path` if intent changed

## Group 4: Reflector + Stats Integration

- [ ] 4.1 In `zsiga/intake/reflector.py` `_scan_metric_degradation()`: after existing metric checks, call `compute_intent_accuracy()` from intent_tracker; if rolling accuracy (last 20) < 60%, emit a `metric_degradation` signal; if any single intent type accuracy < 50%, emit per-type signal
- [ ] 4.2 In `zsiga/metrics/collector.py` `compute_stats()`: call `compute_intent_accuracy()` and add `intent_accuracy_pct`, `intent_accuracy_by_type`, `intent_low_confidence_count` to the returned stats dict
- [ ] 4.3 Add reflector intent accuracy signal tests to `tests/test_reflector.py` — cover: low accuracy triggers signal, healthy accuracy no signal, per-intent-type signal, empty table no signal
