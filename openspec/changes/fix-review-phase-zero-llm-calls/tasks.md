# Tasks: Fix Review Phase Zero LLM Calls

## Group 1: ReviewLoopResult Metrics Fields

- [ ] **1.1** Add `llm_calls`, `tool_calls`, `prompt_tokens`, `completion_tokens` fields to `ReviewLoopResult` dataclass in `zsiga/agent/reviewer.py` (all default to 0)

## Group 2: Capture Metrics in run_review_loop

- [ ] **2.1** In `run_review_loop()`, capture the `SubAgentResult` returned by `run_review()` and accumulate its `llm_calls`/`tool_calls`/`prompt_tokens`/`completion_tokens` into running totals each round
- [ ] **2.2** In `run_review_loop()`, capture the `RunResult` returned by `agent.run()` (fix attempt for CRITICAL issues) and accumulate its metrics into the same running totals
- [ ] **2.3** Set the accumulated totals on the `ReviewLoopResult` returned from `run_review_loop()` for all exit paths (CLEAN, UNKNOWN, SUGGESTION-only, ISSUES_FOUND after max rounds)

## Group 3: Wire Metrics into Orchestrator PhaseRecord

- [ ] **3.1** In `zsiga/pipeline/orchestrator.py` `_run_phases()`, pass `review_result.llm_calls`, `review_result.tool_calls`, `review_result.prompt_tokens`, `review_result.completion_tokens` into the review `PhaseRecord` constructor

## Group 4: Tests

- [ ] **4.1** Update `TestReviewLoopResult` in `tests/test_reviewer.py` to verify new metrics fields default to 0 and are set correctly
