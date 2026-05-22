# Spec: Feedback Loop Metrics Data Collection

## ADDED Requirements

### Requirement: collect_feedback_loop_metrics function

The system SHALL provide a function `collect_feedback_loop_metrics` in `zsiga/metrics/dashboard.py` that returns a structured dictionary containing four feedback loop health indicators: Learnings Health, Learning Injection Rate, Auto-Proposal Success Rate, and Self-Assessment Coverage.

The function SHALL accept an optional `db_path` parameter (for testability) and SHALL read data from:
- `memory/learnings.jsonl` for learnings count, pattern distribution, and last write timestamp
- `data/zsiga.db` (or provided `db_path`) `changes` table for auto-proposal statistics
- `data/zsiga.db` `self_assessment` table for coverage data
- `data/zsiga.db` `injection_events` table for injection rate data

#### Scenario: Returns full metrics dict when all data sources exist

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a temporary sqlite database with changes, self_assessment, injection_events rows, and a temporary learnings.jsonl with valid entries
- **When** `collect_feedback_loop_metrics(db_path=tmp_db, learnings_path=tmp_learnings)` is called
- **Then** the returned dict SHALL contain keys `learnings_health`, `injection_rate`, `auto_proposal_success`, `self_assessment_coverage`, each being a non-empty dict with expected sub-keys

#### Scenario: Returns zero-value structure when learnings.jsonl does not exist

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a temporary sqlite database with schema but no data, and a non-existent learnings file path
- **When** `collect_feedback_loop_metrics(db_path=tmp_db, learnings_path=nonexistent_path)` is called
- **Then** the returned dict SHALL contain all four top-level keys with safe zero/default values, and the function SHALL NOT raise an exception

#### Scenario: Returns zero-value structure when database tables are empty

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a temporary sqlite database with tables created but containing zero rows, and a non-existent learnings file
- **When** `collect_feedback_loop_metrics(db_path=tmp_db, learnings_path=nonexistent_path)` is called
- **Then** the returned dict SHALL have `learnings_health.total_count` == 0, `auto_proposal_success.total` == 0, `self_assessment_coverage.total_changes` == 0

### Requirement: learnings_health metric structure

The `learnings_health` sub-dict SHALL contain:
- `total_count` (int): total number of lessons in learnings.jsonl
- `pattern_distribution` (dict[str, int]): top 5 pattern_key → count mapping
- `last_written` (str): ISO timestamp of most recent learning entry, or empty string if none

#### Scenario: Pattern distribution returns top 5 keys by count

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a learnings.jsonl file with entries having pattern_keys "a" (10 times), "b" (8 times), "c" (6 times), "d" (4 times), "e" (2 times), "f" (1 time)
- **When** `collect_feedback_loop_metrics` is called
- **Then** `learnings_health.pattern_distribution` SHALL contain exactly 5 entries for keys "a" through "e", and SHALL NOT contain "f"

### Requirement: auto_proposal_success metric structure

The `auto_proposal_success` sub-dict SHALL contain:
- `total` (int): total number of changes
- `success` (int): number with outcome "success"
- `failed` (int): number with outcome "reverted"
- `stuck` (int): number of changes with ≥3 FAIL phase records
- `success_rate_pct` (float): success / total * 100, rounded to 1 decimal; 0.0 when total is 0

#### Scenario: Stuck count identifies changes with 3+ failed phases

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a database with 1 change having 3 phase records with outcome "fail" and 1 change with 1 phase record with outcome "success"
- **When** `collect_feedback_loop_metrics` is called
- **Then** `auto_proposal_success.stuck` SHALL be 1 and `auto_proposal_success.success` SHALL be 1

### Requirement: self_assessment_coverage metric structure

The `self_assessment_coverage` sub-dict SHALL contain:
- `total_changes` (int): total changes from changes table
- `assessed_changes` (int): number of distinct change_name values in self_assessment table
- `coverage_pct` (float): assessed_changes / total_changes * 100, rounded to 1 decimal; 0.0 when total is 0
- `last_assessed` (str): ISO timestamp of most recent self_assessment row, or empty string

#### Scenario: Coverage percentage computed from distinct change names

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a database with 10 changes and 7 distinct change_names in self_assessment
- **When** `collect_feedback_loop_metrics` is called
- **Then** `self_assessment_coverage.coverage_pct` SHALL be 70.0
