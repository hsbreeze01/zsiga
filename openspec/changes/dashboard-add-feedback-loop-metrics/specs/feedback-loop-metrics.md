# Delta Spec: Feedback Loop Metrics Calculation Layer

## ADDED Requirements

### Requirement: Learnings Health Metric

The system SHALL provide a function `compute_learnings_health` that reads `memory/learnings.jsonl` and returns a structured dict containing:

- `total` (int): total number of learning entries
- `active` (int): count of entries not marked as suppressed/cleaned
- `top_patterns` (list of `{pattern_key: str, count: int}`): top 5 pattern_key by frequency, sorted descending
- `last_write` (str | None): ISO-8601 timestamp of the most recent learning entry, or None if no entries

When `memory/learnings.jsonl` does not exist or is empty, the function SHALL return `{total: 0, active: 0, top_patterns: [], last_write: None}` without raising an exception.

#### Scenario: Compute metrics from a populated learnings file

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_learnings_health
- **Given** a temporary `memory/learnings.jsonl` file containing 10 valid JSONL entries, each with at least `pattern_key` and `timestamp` fields, where 3 entries share pattern_key `"daemon.cycle_error"` and the remaining 7 have distinct pattern keys
- **When** `compute_learnings_health` is called with the path to that file
- **Then** the returned dict has `total == 10`, `active == 10`, `top_patterns[0]["pattern_key"] == "daemon.cycle_error"` and `top_patterns[0]["count"] == 3`, and `last_write` is an ISO-8601 string

#### Scenario: Compute metrics from missing learnings file

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_learnings_health
- **Given** a path to a file that does not exist
- **When** `compute_learnings_health` is called with that path
- **Then** the returned dict is `{total: 0, active: 0, top_patterns: [], last_write: None}` and no exception is raised

#### Scenario: Compute metrics from empty learnings file

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_learnings_health
- **Given** a `memory/learnings.jsonl` file that exists but contains zero lines
- **When** `compute_learnings_health` is called with the path to that file
- **Then** the returned dict is `{total: 0, active: 0, top_patterns: [], last_write: None}`

---

### Requirement: Learning Injection Rate Metric

The system SHALL provide a function `compute_injection_rate` that reads the `learning_injections` table from `data/zsiga.db` and returns:

- `implement_rate` (str): `"N/A"` if no IMPLEMENT phases, else `"X/Y (P%)"` where X = IMPLEMENT phases with injections, Y = total IMPLEMENT phases, P = percentage
- `enrich_rate` (str): same format for ENRICH phases
- `avg_injected` (float | None): average `injected_count` across all injection records, or None if no records

When the table does not exist or contains no rows, the function SHALL return `{implement_rate: "N/A", enrich_rate: "N/A", avg_injected: None}` without raising.

#### Scenario: Compute injection rate with mixed data

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_injection_rate
- **Given** an in-memory SQLite database with a `learning_injections` table containing 4 rows: 2 with `phase == "IMPLEMENT"` (injected_count 3 and 0), 2 with `phase == "ENRICH"` (injected_count 5 and 2)
- **When** `compute_injection_rate` is called with a connection to that database
- **Then** `implement_rate` contains `"1/2 (50%)"`, `enrich_rate` contains `"2/2 (100%)"`, and `avg_injected == 2.5`

#### Scenario: Compute injection rate with empty table

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_injection_rate
- **Given** an in-memory SQLite database with a `learning_injections` table containing zero rows
- **When** `compute_injection_rate` is called with a connection to that database
- **Then** the returned dict is `{implement_rate: "N/A", enrich_rate: "N/A", avg_injected: None}`

#### Scenario: Compute injection rate when table does not exist

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_injection_rate
- **Given** an in-memory SQLite database with no `learning_injections` table
- **When** `compute_injection_rate` is called with a connection to that database
- **Then** the returned dict is `{implement_rate: "N/A", enrich_rate: "N/A", avg_injected: None}` and no exception is raised

---

### Requirement: Auto-Proposal Success Rate Metric

The system SHALL provide a function `compute_auto_proposal_success` that reads the `changes` table from `data/zsiga.db` and returns:

- `total` (int): total auto-generated proposals (where source indicates auto-generation)
- `success` (int): proposals that reached a terminal success state
- `failed` (int): proposals that reached a terminal failure state
- `stuck` (int): proposals with ≥3 FAIL attempts
- `success_rate` (str): `"N/A"` if total == 0, else `"P%"` formatted percentage
- `stuck_list` (list of str): change_ids of stuck proposals

When the table does not exist or has no matching rows, the function SHALL return safe zero values with `success_rate == "N/A"` and `stuck_list == []`.

#### Scenario: Compute auto-proposal success with varied outcomes

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_auto_proposal_success
- **Given** an in-memory SQLite database with a `changes` table containing 5 auto-proposal rows: 2 in success state, 1 in fail state, 2 each with 3+ fail-attempt records (stuck)
- **When** `compute_auto_proposal_success` is called with a connection to that database
- **Then** `total == 5`, `success == 2`, `failed == 1`, `stuck == 2`, `success_rate` is a percentage string, and `stuck_list` contains 2 change_id strings

#### Scenario: Compute auto-proposal success with empty changes

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_auto_proposal_success
- **Given** an in-memory SQLite database with a `changes` table containing zero auto-proposal rows
- **When** `compute_auto_proposal_success` is called with a connection to that database
- **Then** `total == 0`, `success_rate == "N/A"`, `stuck_list == []`

---

### Requirement: Self-Assessment Coverage Metric

The system SHALL provide a function `compute_self_assessment_coverage` that reads the `changes` and `self_assessment` tables from `data/zsiga.db` and returns:

- `total_changes` (int): total changes in the changes table
- `assessed` (int): number of changes with at least one self_assessment record
- `coverage` (str): `"N/A"` if total == 0, else `"P%"` formatted
- `last_assessment` (str | None): ISO-8601 timestamp of the most recent self_assessment, or None

When tables do not exist or are empty, the function SHALL return `{total_changes: 0, assessed: 0, coverage: "N/A", last_assessment: None}`.

#### Scenario: Compute self-assessment coverage with partial data

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_self_assessment_coverage
- **Given** an in-memory SQLite database with a `changes` table containing 4 rows and a `self_assessment` table containing records for 3 of those changes (by change_id), with the most recent assessment timestamp being `"2025-06-01T12:00:00"`
- **When** `compute_self_assessment_coverage` is called with a connection to that database
- **Then** `total_changes == 4`, `assessed == 3`, `coverage == "75%"`, `last_assessment == "2025-06-01T12:00:00"`

#### Scenario: Compute self-assessment coverage with empty tables

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_self_assessment_coverage
- **Given** an in-memory SQLite database with empty `changes` and `self_assessment` tables
- **When** `compute_self_assessment_coverage` is called with a connection to that database
- **Then** `total_changes == 0`, `assessed == 0`, `coverage == "N/A"`, `last_assessment is None`

---

### Requirement: Aggregate Feedback Metrics Function

The system SHALL provide a function `compute_all_feedback_metrics` that orchestrates the 4 individual metric functions and returns a single dict with keys `learnings_health`, `injection_rate`, `auto_proposal_success`, `self_assessment_coverage`, each containing the respective metric dict.

If any individual metric function raises an exception, `compute_all_feedback_metrics` SHALL catch it and substitute a safe default (zero values / "N/A" / empty lists) for that metric, without propagating the exception.

#### Scenario: Aggregate metrics with all valid data sources

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_all_feedback_metrics
- **Given** a temporary file system with a valid `learnings.jsonl` and an in-memory SQLite database with populated tables
- **When** `compute_all_feedback_metrics` is called with paths to both data sources
- **Then** the returned dict contains all 4 keys (`learnings_health`, `injection_rate`, `auto_proposal_success`, `self_assessment_coverage`) and each sub-dict has the expected structure with non-zero values

#### Scenario: Aggregate metrics with missing data sources

- **testable**: true
- **target**: zsiga/feedback_loop_metrics.py::compute_all_feedback_metrics
- **Given** a path to a non-existent `learnings.jsonl` and an empty in-memory SQLite database (no relevant tables)
- **When** `compute_all_feedback_metrics` is called with those paths
- **Then** the returned dict contains all 4 keys, and each sub-dict contains safe defaults (zero counts, "N/A" rates, None timestamps, empty lists) without any exception being raised
