# Spec: Verify Pass Rate Metric Script

## Problem

There is no standalone script to compute and display `verify_pass_rate` with
breakdowns, trends, and root-cause categories. The metric is currently only
visible through `compute_stats()` which gives a single aggregate number.

## ADDED Requirements

### Requirement: compute_verify_rate_report SHALL produce structured metric report

A function `compute_verify_rate_report` at `zsiga/metrics/verify_rate.py` SHALL
accept a list of change dicts (same format as `changes.jsonl` entries) and
return a structured dict containing:

1. `verify_pass_rate_pct` — overall verify pass rate as a float percentage
2. `by_project` — dict of `{project_name: pass_rate_pct}` for each project
3. `failure_breakdown` — dict of `{category: count}` using failure_category values
4. `rolling_window` — list of `{window_end: date, rate: float}` entries

Only changes that have at least one verify-phase record SHALL be counted toward
the rate. Pass rate is computed as `(verify_success_count / total_verify_count) * 100`.

#### Scenario: Report contains overall verify pass rate

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** 3 changes: 2 with verify outcome "success", 1 with verify outcome "fail"
- **When** `compute_verify_rate_report` is called
- **Then** `report["verify_pass_rate_pct"]` SHALL be approximately `66.7` (±0.2)

#### Scenario: Report contains per-project breakdown

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** changes from projects "zsiga" and "compass", each with both pass and fail verify outcomes
- **When** `compute_verify_rate_report` is called
- **Then** `report["by_project"]` SHALL contain keys for both `"zsiga"` and `"compass"` with float percentage values

#### Scenario: Report contains failure breakdown by category

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** 4 verify-fail changes with `failure_category` values: 2 × `"unknown"`, 1 × `"llm_judge"`, 1 × `"lint"`
- **When** `compute_verify_rate_report` is called
- **Then** `report["failure_breakdown"]` SHALL be `{"unknown": 2, "llm_judge": 1, "lint": 1}`

#### Scenario: Report handles empty change list gracefully

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** an empty list of changes
- **When** `compute_verify_rate_report` is called
- **Then** `report["verify_pass_rate_pct"]` SHALL be `0.0`
- **And** `report["by_project"]` SHALL be `{}`
- **And** `report["failure_breakdown"]` SHALL be `{}`
- **And** `report["rolling_window"]` SHALL be `[]`
