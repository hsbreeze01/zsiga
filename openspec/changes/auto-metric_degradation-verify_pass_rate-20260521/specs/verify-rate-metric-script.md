# Spec: Verify Pass Rate Metric Script

## Problem

There is no standalone script to compute and display `verify_pass_rate` with
breakdowns, trends, and root-cause categories. The metric is currently only
visible through `compute_stats()` which gives a single aggregate number.

## ADDED Requirements

### Requirement: CLI metric script for verify pass rate analysis

A script at `zsiga/metrics/verify_rate.py` SHALL provide a `compute_verify_rate_report`
function that returns a structured dict containing:

1. `verify_pass_rate_pct` — overall rate
2. `by_project` — dict of `{project_name: pass_rate_pct}`
3. `failure_breakdown` — dict of `{category: count}` using the classification
4. `rolling_window` — list of `{window_end: date, rate: float}` for the last N changes (default N=20)
5. `top_failure_patterns` — list of `{category, count, recent_examples: [change_name]}`

#### Scenario: Report contains overall verify pass rate

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** 128 historical changes with 63 verify-phase successes
- **When** `compute_verify_rate_report` is called
- **Then** `report["verify_pass_rate_pct"]` SHALL equal `49.2`

#### Scenario: Report contains per-project breakdown

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** changes from projects "zsiga" (70 verify phases, 26 pass) and "compass" (28 verify phases, 20 pass)
- **When** `compute_verify_rate_report` is called
- **Then** `report["by_project"]["zsiga"]` SHALL be `37.1` (±0.2)
- **And** `report["by_project"]["compass"]` SHALL be `71.4` (±0.2)

#### Scenario: Report contains failure breakdown by category

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** verify phases with `failure_category` values: 20 `"unknown"`, 10 `"llm_judge"`, 8 `"lint"`
- **When** `compute_verify_rate_report` is called
- **Then** `report["failure_breakdown"]` SHALL be `{"unknown": 20, "llm_judge": 10, "lint": 8}`

#### Scenario: Report handles empty change list gracefully

- **testable**: true
- **target**: zsiga/metrics/verify_rate.py::compute_verify_rate_report
- **Given** an empty list of changes
- **When** `compute_verify_rate_report` is called
- **Then** `report["verify_pass_rate_pct"]` SHALL be `0.0`
- **And** `report["by_project"]` SHALL be `{}`
- **And** `report["failure_breakdown"]` SHALL be `{}`
- **And** `report["rolling_window"]` SHALL be `[]`
