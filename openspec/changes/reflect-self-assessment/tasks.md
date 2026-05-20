# Tasks: Self-Assessment Phase (REFLECT)

## Group 1: Data Layer

- [x] **1.1** Add `self_assessment` table and accessor functions in `metrics/db.py`
  - Add `self_assessment` table to `_SCHEMA` with columns: id, change_name, task_type, predicted_tokens, actual_tokens, predicted_steps, actual_steps, fix_attempts, outcome, self_rating, strengths, weaknesses, lessons, created_at
  - Add `record_self_assessment(row: dict, db_path=None)` function
  - Add `query_self_assessment_stats(task_type: str, limit: int = 10, db_path=None) -> dict` function returning `{avg_tokens, avg_steps, success_rate, count}` or `{count: 0}` when no data
  - Add `query_recent_ratings(task_type: str, limit: int = 3, db_path=None) -> list[str]` function for boundary detection

- [x] **1.2** Add `REFLECT = "reflect"` to `Phase` enum in `metrics/types.py`
  - Extend the existing `Phase` enum with the new value so PhaseRecord can represent the REFLECT phase

## Group 2: Orchestrator Integration

- [ ] **2.1** Implement `phase_reflect()` method in `pipeline/orchestrator.py`
  - Accept parameters: `rec` (ChangeRecord), `change_name`, `project_name`, `task_type` (str), `change_dir`, `transport`
  - Compute `total_fix_attempts` from rec.phases (sum of fix_attempts in IMPLEMENT + VERIFY)
  - Compute `actual_tokens` = sum of (prompt_tokens + completion_tokens) across all phases
  - Compute `actual_steps` = sum of (llm_calls + tool_calls) across all phases
  - Determine `self_rating` using the rating algorithm (excellent/good/average/poor)
  - Build `strengths` and `weaknesses` lists using rule-based heuristics
  - Build `lessons` list from phase detail fields and fix history
  - Call `record_self_assessment()` to persist to DB
  - Check capability boundary: call `query_recent_ratings(task_type, limit=3)`, if all 3 are "poor" → `record_lesson()`
  - Generate `reflect.md` content and write to `change_dir` via transport
  - Append `PhaseRecord(phase=Phase.REFLECT, outcome=Outcome.SUCCESS)` to `rec.phases`
  - Return elapsed time for logging

- [ ] **2.2** Wire REFLECT phase into `_run_phases()` in `pipeline/orchestrator.py`
  - Pass `intent` through to `_run_phases()` (currently not passed — add parameter)
  - Derive `task_type` from `intent.intent_type` using INTENT_TO_TASK_TYPE mapping
  - After VERIFY success (before DELIVER), call `self.phase_reflect(...)`
  - Print phase header and timing, matching the pattern of other phases
  - On reverted changes (VERIFY fail path), skip REFLECT entirely

## Group 3: Tests

- [ ] **3.1** Create `tests/test_self_assessment.py` with comprehensive test coverage
  - Test `record_self_assessment` and `query_self_assessment_stats` DB functions (using tmp_path db)
  - Test `query_recent_ratings` returns correct rating list and handles empty case
  - Test self-rating algorithm: excellent (0 fix, success), good (≤2 fix, success), average (≤5 fix, success), poor (reverted or >5 fix)
  - Test reflect.md content contains required sections
  - Test capability boundary detection: 3 consecutive poor triggers lesson, mixed ratings do not
  - Test `phase_reflect()` integration: PhaseRecord appended, DB row created, reflect.md written
  - Test REFLECT phase is skipped on reverted changes
