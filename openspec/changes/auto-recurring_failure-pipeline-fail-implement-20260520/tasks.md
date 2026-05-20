# Tasks: Fix Recurring `pipeline.fail.implement` Pattern

## Group 1: Lint Prevention in Implementer

- [x] 1.1 Add `## Lint Prevention Rules` section to `IMPLEMENTER_SYSTEM` constant in `zsiga/pipeline/implementer.py` — lists forbidden patterns (E701, E702, E401, E741) with correct/incorrect examples, and instructs the agent to never write these patterns

## Group 2: Pattern Warning Injection

- [x] 2.1 Add `_build_pattern_warnings()` helper in `zsiga/pipeline/implementer.py` — calls `pattern_miner.mine_patterns()`, filters to `pipeline.fail.*` keys with severity "high", formats top-3 as a markdown warning section, returns empty string if none
- [x] 2.2 Integrate `_build_pattern_warnings()` into `implement()` function — append the warning section to `user_prompt` before passing to `agent.run()`
- [x] 2.3 Add unit test for `_build_pattern_warnings()` in a new test file `tests/test_implementer_warnings.py` — verify: returns empty string when no high-severity patterns exist; returns formatted markdown when patterns exist; limits to top-3 warnings
