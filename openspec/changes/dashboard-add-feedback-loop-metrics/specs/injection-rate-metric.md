# Spec: Injection Rate Metric in Feedback Loop

## ADDED Requirements

### Requirement: injection_rate metric in collect_feedback_loop_metrics

The `injection_rate` sub-dict returned by `collect_feedback_loop_metrics` SHALL contain:
- `by_phase` (dict[str, dict]): mapping phase name → {"event_count": int, "total_injected": int, "rate_pct": float}
  - `rate_pct` = event_count / total_phase_runs * 100 where total_phase_runs is the count of phase records for that phase in the changes table
- `avg_injected` (float): average injected_count across all injection events; 0.0 when no events

#### Scenario: injection_rate computed from injection_events and phase records

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a database with 10 "implement" phase records in changes, and 7 injection_events with phase "implement"
- **When** `collect_feedback_loop_metrics` is called
- **Then** `injection_rate.by_phase["implement"]["rate_pct"]` SHALL be 70.0

#### Scenario: injection_rate returns empty when no injection events

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/dashboard.py::collect_feedback_loop_metrics
- **Given** a database with no injection_events rows
- **When** `collect_feedback_loop_metrics` is called
- **Then** `injection_rate.by_phase` SHALL be an empty dict and `injection_rate.avg_injected` SHALL be 0.0

