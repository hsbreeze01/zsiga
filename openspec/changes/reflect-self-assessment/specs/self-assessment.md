# Spec: Self-Assessment Phase (REFLECT)

## ADDED Requirements

### REQ-SA-01: REFLECT Phase in Pipeline

The pipeline SHALL include a REFLECT phase executed after VERIFY and before DELIVER.
REFLECT is a read-only evaluation phase that MUST NOT modify any project source files.

#### Scenario: Successful pipeline includes REFLECT phase

- Given a change with IMPLEMENT and VERIFY phases both passing
- When the pipeline proceeds to DELIVER
- Then a REFLECT phase SHALL have been executed between VERIFY and DELIVER
- And the REFLECT phase outcome SHALL be recorded in the ChangeRecord

#### Scenario: REFLECT phase is skipped when VERIFY fails and change is reverted

- Given a change where VERIFY fails and causes a revert
- When the pipeline reverts to the pre-implementation SHA
- Then the REFLECT phase SHALL NOT be executed
- And no reflect.md SHALL be generated

### REQ-SA-02: Self-Assessment Report (reflect.md)

The REFLECT phase SHALL produce a `reflect.md` file in the change directory containing:
1. **Task Review**: actual vs predicted metrics (token consumption, time, steps, fix_attempts)
2. **Self-Rating**: one of `excellent`, `good`, `average`, `poor`
3. **Strengths**: list of aspects performed well
4. **Weaknesses**: list of aspects that need improvement
5. **Lessons Learned**: key decisions, failure reasons (if any), improvement suggestions
6. **Next Time Suggestions**: predicted token estimate for similar tasks, constraints to watch

The self-rating SHALL be computed from objective metrics:
- `excellent`: zero fix_attempts across all phases
- `good`: total fix_attempts ≤ 2 and outcome is success
- `average`: total fix_attempts ≤ 5 and outcome is success
- `poor`: outcome is reverted OR total fix_attempts > 5

#### Scenario: Self-rating is excellent for first-pass success

- Given a change with zero fix_attempts in IMPLEMENT and VERIFY phases
- And the outcome is success
- When REFLECT computes the self-rating
- Then the self-rating SHALL be `excellent`

#### Scenario: Self-rating is poor for reverted change

- Given a change that was reverted during VERIFY
- When REFLECT computes the self-rating
- Then the self-rating SHALL be `poor`

#### Scenario: reflect.md is written to change directory

- Given a completed REFLECT phase
- When the reflect.md is generated
- Then the file SHALL exist in the change directory
- And SHALL contain sections for Task Review, Self-Rating, Strengths, Weaknesses, Lessons Learned, and Next Time Suggestions

### REQ-SA-03: Self-Assessment Database Table

A `self_assessment` table SHALL be created in `zsiga.db` with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| change_name | TEXT | Change identifier |
| task_type | TEXT | One of: `fix`, `impl`, `refactor` (derived from intent classification) |
| predicted_tokens | INTEGER | Tokens predicted at CLARIFY time (0 if unavailable) |
| actual_tokens | INTEGER | Sum of prompt_tokens + completion_tokens across all phases |
| predicted_steps | INTEGER | Steps predicted at CLARIFY time (0 if unavailable) |
| actual_steps | INTEGER | Sum of llm_calls + tool_calls across all phases |
| fix_attempts | INTEGER | Total fix_attempts across IMPLEMENT and VERIFY |
| outcome | TEXT | One of: `success`, `reverted`, `partial` |
| self_rating | TEXT | One of: `excellent`, `good`, `average`, `poor` |
| strengths | TEXT | JSON array of strings |
| weaknesses | TEXT | JSON array of strings |
| lessons | TEXT | JSON array of strings |
| created_at | TEXT | ISO timestamp |

#### Scenario: Self-assessment row is written after REFLECT

- Given a completed REFLECT phase for change "add-feature-x"
- When the self-assessment data is persisted
- Then a row SHALL exist in the `self_assessment` table with `change_name = "add-feature-x"`
- And `actual_tokens` SHALL equal the sum of all phase token usage

#### Scenario: Table creation is idempotent

- Given an existing `zsiga.db` without a `self_assessment` table
- When the schema is applied
- Then the `self_assessment` table SHALL be created
- And subsequent schema applications SHALL NOT raise errors

### REQ-SA-04: Capability Boundary Detection

When a specific task type (fix/impl/refactor) has 3 or more consecutive `poor` ratings
in the `self_assessment` table, the system SHALL:

1. Record a lesson with `pattern_key = "capability.boundary.{task_type}"`
2. The lesson SHALL recommend human intervention for that task type

#### Scenario: Three consecutive poor ratings trigger boundary detection

- Given 3 consecutive rows in `self_assessment` with `task_type = "fix"` and `self_rating = "poor"`
- When the REFLECT phase completes for the 3rd change
- Then a lesson SHALL be recorded with `pattern_key = "capability.boundary.fix"`
- And the lesson takeaway SHALL contain "human intervention"

#### Scenario: Mixed ratings do not trigger boundary detection

- Given `self_assessment` rows for `task_type = "fix"` with ratings `["poor", "good", "poor"]`
- When the REFLECT phase completes
- Then the boundary detection SHALL NOT trigger for `task_type = "fix"`

### REQ-SA-05: Historical Data Query for Estimation

A function SHALL be provided to query the `self_assessment` table by `task_type`
and return aggregated statistics (average tokens, average steps, success rate)
from the last N entries of the same task type.

This function MUST be available for future use by CLARIFY phase for token prediction,
but CLARIFY integration is out of scope for this change.

#### Scenario: Query returns aggregated stats for a task type

- Given 5 rows in `self_assessment` with `task_type = "impl"`
- When the query function is called with `task_type = "impl"` and `limit = 5`
- Then the result SHALL include `avg_tokens`, `avg_steps`, `success_rate`
- And the result SHALL be computed from exactly those 5 rows

#### Scenario: Query with no matching rows returns empty stats

- Given 0 rows in `self_assessment` with `task_type = "refactor"`
- When the query function is called with `task_type = "refactor"`
- Then the result SHALL indicate no historical data is available
