# Tasks: Intent Router OpenSpec Awareness

## Group 1: Construction Marker Logic (intent_router.py)

- [x] **1.1** Add `_CONSTRUCTION_MARKERS` regex constant and integrate into `classify()` keyword scoring
  - Add `_CONSTRUCTION_MARKERS` regex (新增|面板|模块|功能|卡片|组件|页面|feature|panel|module|component|widget|card|section|展示|显示|图表|dashboard|趋势) after existing keyword patterns
  - In `classify()`, when `invest_matches` is non-empty, check `_CONSTRUCTION_MARKERS.search(text)`. If both match, reduce `invest_score` by 4 (floor 0) before appending to `scores`
  - Scope: `zsiga/agent/intent_router.py` lines ~80–82 (new constant) and ~195–205 (scoring block)

- [x] **1.2** Fix `_verbalize()` to respect construction markers
  - In `_verbalize()`, after the `_INVESTIGATION_KEYWORDS.search(text)` check, add `_CONSTRUCTION_MARKERS.search(text)` guard. When construction markers are present, skip the INVESTIGATION verbalization and fall through to IMPL/EVAL/RESEARCH/ambiguous branches
  - Scope: `zsiga/agent/intent_router.py` `_verbalize()` function (~lines 130–155)

## Group 2: Tests (test_intent_router.py)

- [x] **2.1** Add construction marker test class to `tests/test_intent_router.py`
  - Test: "异常诊断面板" with construction markers → INVESTIGATION score reduced, IMPLEMENTATION wins
  - Test: "排查报错" without construction markers → INVESTIGATION unchanged (regression guard)
  - Test: `_verbalize("新增异常诊断面板")` does NOT contain "排查或调试"
  - Test: `_verbalize("排查一下报错")` DOES contain "排查或调试" (unchanged)
  - Test: `classify("Dashboard 实时监控与异常诊断增强")` returns IMPLEMENTATION
