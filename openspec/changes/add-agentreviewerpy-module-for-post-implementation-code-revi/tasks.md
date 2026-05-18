# Tasks: agent/reviewer.py — Post-Implementation Code Review Loop

## Group 1: Core Reviewer Module

- [ ] Create `zsiga/agent/reviewer.py` with `run_review()` and `parse_review_verdict()` functions
  - `run_review()` dispatches a review-role sub-agent using `create_with_role("review")` from sub_agent.py
  - Provides specs, design, tasks, git diff, and mechanical results as input
  - Sub-agent writes `review.md` in the change directory
  - `parse_review_verdict()` reads `review.md` and returns `(verdict, issues_list)` where issues have severity and description
  - Use existing patterns from `pipeline/verifier.py` (reading specs via `_read_all_specs`, parsing verdict from file)

## Group 2: Metrics & Config Extension

- [ ] Add `REVIEW = "review"` to `Phase` enum in `zsiga/metrics/types.py`
  - Position between IMPLEMENT and VERIFY
  - Verify existing PhaseRecord serialization works with new enum member

- [ ] Add review config fields to `PipelineConfig` in `zsiga/config.py`
  - Fields: `review_max_turns` (10), `review_timeout` (180), `review_max_rounds` (2), `review_fix_max_turns` (6)
  - Parse from `zsiga.yaml` pipeline section with defaults
  - Follow existing pattern for other pipeline config fields (enrich_max_turns, etc.)

## Group 3: Orchestrator Integration

- [ ] Integrate REVIEW phase into `zsiga/pipeline/orchestrator.py` `_run_phases()`
  - Insert REVIEW phase between IMPLEMENT success and VERIFY phase (after mechanical verification passes)
  - Implement `_review_loop()` method: dispatch review → parse verdict → auto-fix if CRITICAL → re-review (up to max_rounds)
  - Auto-fix: reuse main agent with focused prompt from CRITICAL issues, then re-run mechanical verify
  - Record `PhaseRecord(phase=Phase.REVIEW, ...)` for each review round
  - On SUGGESTION-only reviews: log and proceed to VERIFY without auto-fix
  - On max rounds exhausted: proceed to VERIFY, record lesson via `record_lesson`
  - Skip REVIEW entirely when mechanical verification fails (existing fix_loop handles that)
  - Update phase numbering: ENRICH(1/5), IMPLEMENT(2/5), REVIEW(3/5), VERIFY(4/5), DELIVER(5/5)

## Group 4: Tests

- [ ] Create `tests/test_reviewer.py` with unit tests for the reviewer module
  - Test `parse_review_verdict()` with CLEAN verdict
  - Test `parse_review_verdict()` with ISSUES_FOUND + CRITICAL issues
  - Test `parse_review_verdict()` with ISSUES_FOUND + SUGGESTION-only issues
  - Test `parse_review_verdict()` with malformed/missing review.md (returns UNKNOWN + empty list)
  - Test `parse_review_verdict()` with mixed CRITICAL and SUGGESTION issues
