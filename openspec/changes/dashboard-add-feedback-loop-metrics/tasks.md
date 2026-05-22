# Tasks: dashboard-add-feedback-loop-metrics

## 1. Feedback Loop Computation Layer
- [x] 1.1 Implement `compute_learnings_health()` — total, active (excl. noise), top-5 pattern_keys, last write timestamp
- [x] 1.2 Implement `compute_injection_rate()` — IMPLEMENT rate, ENRICH rate, avg per session
- [x] 1.3 Implement `compute_auto_proposal_rate()` — total, success, reverted, stuck (>=3 fails), success rate
- [x] 1.4 Implement `compute_self_assessment_coverage()` — total changes, assessed, coverage %, last assessment

## 2. Dashboard Rendering
- [x] 2.1 Add `_render_feedback_loop()` to dashboard.py — renders Feedback Loop section with 4 cards, "No data" fallbacks
- [x] 2.2 Integrate `_render_feedback_loop()` into `_render()` — section appears between Journal and Recent Changes

## 3. Test Coverage
- [x] 3.1 Test computation functions with data present and empty states
- [x] 3.2 Test rendering HTML output for section presence, card titles, and empty-state fallback messages
