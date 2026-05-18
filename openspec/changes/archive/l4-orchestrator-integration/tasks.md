# Tasks: L4 Orchestrator Integration

## 1. Intent Router Integration

- [ ] 1.1 Add intent classification at the top of `_process_change()` — import `intent_router.classify` and `intent_router.route`, read proposal.md content, call `classify()`, log the result (intent type + confidence + route path), and skip non-pipeline intents (`TRIVIAL`/`EXPLORATION`/`AMBIGUOUS` when route is not `"pipeline"`)

## 2. Task Decomposition Integration

- [ ] 2.1 Add cross-project decomposition support in `run_cycle()` — import `task_decomposer.decompose` and `task_decomposer.aggregate_results`, detect multi-project proposals by calling `decompose(proposal_text, available_projects)`, and when multiple subtasks are generated dispatch each via `_process_change()` with synthetic proposal dicts, then aggregate and log results

## 3. Escalation Protocol Integration

- [ ] 3.1 Integrate `EscalationManager` into `_run_phases()` — import `EscalationManager`, create instance at the top of `_run_phases()` with `change_name` and `persist_dir=change_dir`, pass the manager to `_fix_loop()` and `_eval_fix_loop()`

- [ ] 3.2 Add failure recording and strategy-aware fix prompts in `_fix_loop()` — after each failed attempt call `escalation.record_failure(errors, phase="implement", strategy=current_strategy)`, check `should_escalate()` to modify the system prompt with strategy rotation instructions, and check `should_abort()` to break early and return `(False, attempts)`

- [ ] 3.3 Add failure recording in `_eval_fix_loop()` — after each failed attempt call `escalation.record_failure(feedback, phase="verify", strategy=current_strategy)`, with the same strategy rotation and abort logic as the implement fix loop

- [ ] 3.4 Add escalation-based diagnosis and revert in `_run_phases()` — when `_fix_loop()` or `_eval_fix_loop()` returns `False` with `should_abort()`, call `escalation.generate_diagnosis()`, save the report to the change directory, record a lesson with `pattern_key="pipeline.fail.escalation"`, then revert

## 4. Integration Tests

- [ ] 4.1 Add `tests/test_l4_integration.py` with tests for: (a) intent classification skipping non-pipeline proposals, (b) cross-project decomposition dispatch and aggregation, (c) escalation manager lifecycle across fix loops with strategy rotation, (d) auto-abort after max failures with diagnosis report generation
