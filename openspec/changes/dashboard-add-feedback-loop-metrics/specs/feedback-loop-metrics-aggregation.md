# Spec: Feedback Loop Metrics Aggregation

## ADDED Requirements

### Requirement: compute_feedback_metrics function

A new function `compute_feedback_metrics(db_path=None) -> dict` SHALL be added to `zsiga/metrics/collector.py` (or a new module `zsiga/metrics/feedback.py` imported by dashboard.py) that computes four feedback-loop health indicators from the existing data sources (lessons table, changes table, self_assessment table) and returns a structured dict.

The returned dict SHALL have exactly these top-level keys:

```python
{
    "learnings_health": {
        "total": int,
        "top_patterns": list[tuple[str, int]],  # top 5 (pattern_key, count)
        "last_write_ts": str,                    # ISO timestamp or ""
    },
    "injection_rate": {
        "implement_rate_pct": float,   # % of IMPLEMENT phases that had learnings injected
        "enrich_rate_pct": float,       # % of ENRICH phases that had learnings injected
        "avg_lessons_per_session": float,
    },
    "auto_proposal_success": {
        "total": int,
        "success": int,
        "reverted": int,
        "stuck": int,   # >=3 fail phases
        "success_rate_pct": float,
    },
    "self_assessment_coverage": {
        "total_changes": int,
        "assessed_changes": int,
        "coverage_pct": float,
        "last_assessment_ts": str,  # ISO timestamp or ""
    },
}
```

#### Scenario: Empty database returns safe defaults

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a fresh sqlite3 database with zero rows in lessons, changes, and self_assessment tables
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** the returned dict SHALL contain all four top-level keys with numeric values defaulting to 0 and empty lists/strings where applicable:
  - `learnings_health.total` == 0
  - `learnings_health.top_patterns` == []
  - `learnings_health.last_write_ts` == ""
  - `injection_rate.implement_rate_pct` == 0.0
  - `injection_rate.enrich_rate_pct` == 0.0
  - `injection_rate.avg_lessons_per_session` == 0.0
  - `auto_proposal_success.total` == 0
  - `auto_proposal_success.success` == 0
  - `auto_proposal_success.reverted` == 0
  - `auto_proposal_success.stuck` == 0
  - `auto_proposal_success.success_rate_pct` == 0.0
  - `self_assessment_coverage.total_changes` == 0
  - `self_assessment_coverage.assessed_changes` == 0
  - `self_assessment_coverage.coverage_pct` == 0.0
  - `self_assessment_coverage.last_assessment_ts` == ""

#### Scenario: Learnings health computed from lessons table

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a sqlite3 database with 10 lesson rows, 3 with `pattern_key = "pipeline.fail.implement"`, 2 with `pattern_key = "code.unknown"`, 5 with distinct other pattern keys, and the most recent `created_at` is `"2026-06-01T12:00:00"`
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** `learnings_health.total` SHALL be 10, `learnings_health.top_patterns` SHALL contain `("pipeline.fail.implement", 3)` as the first entry, and `learnings_health.last_write_ts` SHALL equal `"2026-06-01T12:00:00"`

#### Scenario: Auto-proposal success rate from changes table

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a sqlite3 database with 5 change records whose `change_name` starts with `"auto-"`: 2 with `outcome = "success"`, 2 with `outcome = "reverted"`, 1 with `outcome = "reverted"` and 3+ phases having `outcome = "fail"` (stuck)
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** `auto_proposal_success.total` SHALL be 5, `auto_proposal_success.success` SHALL be 2, `auto_proposal_success.reverted` SHALL be 3, `auto_proposal_success.stuck` SHALL be 1, and `auto_proposal_success.success_rate_pct` SHALL be 40.0

#### Scenario: Self-assessment coverage from self_assessment and changes tables

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a sqlite3 database with 10 change records and 4 self_assessment records covering 4 distinct change_names
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** `self_assessment_coverage.total_changes` SHALL be 10, `self_assessment_coverage.assessed_changes` SHALL be 4, and `self_assessment_coverage.coverage_pct` SHALL be 40.0

#### Scenario: Injection rate derived from lessons_count and phase data

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a sqlite3 database with 5 change records, each having an IMPLEMENT phase; 3 of those changes have `lessons_count > 0`; 4 changes have an ENRICH phase with 2 having `lessons_count > 0`; total lessons across all changes = 15
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** `injection_rate.implement_rate_pct` SHALL be 60.0, `injection_rate.enrich_rate_pct` SHALL be 50.0, and `injection_rate.avg_lessons_per_session` SHALL be 3.0 (15 / 5 changes with lessons)

#### Scenario: Malformed phases_json handled gracefully

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a sqlite3 database with a change record whose `phases_json` is `"not valid json"`
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** the function SHALL NOT raise an exception; the malformed record SHALL be skipped and all metric values SHALL reflect only the valid records

### Requirement: Non-auto proposals excluded from auto_proposal_success

The `auto_proposal_success` metric SHALL only count changes whose `change_name` starts with `"auto-"`. Changes with other prefixes SHALL be excluded from this metric entirely.

#### Scenario: Mixed auto and non-auto changes

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a sqlite3 database with 8 change records: 3 starting with `"auto-"` (all success), 5 with other names (mix of success/reverted)
- **When** `compute_feedback_metrics(db_path=<path>)` is called
- **Then** `auto_proposal_success.total` SHALL be 3 and `auto_proposal_success.success` SHALL be 3

### Requirement: DB path parameter for testability

`compute_feedback_metrics` SHALL accept an optional `db_path` parameter (same pattern as all other DB functions in `zsiga/metrics/db.py`), defaulting to `None` (which uses the production `_DB_PATH`).

#### Scenario: Custom db_path used

- **testable**: true
- **target**: zsiga.metrics.feedback.compute_feedback_metrics
- **Given** a temporary sqlite3 database at `/tmp/test_zsiga.db` with known data
- **When** `compute_feedback_metrics(db_path=Path("/tmp/test_zsiga.db"))` is called
- **Then** the metrics SHALL reflect data from the temporary database, not the production one

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
