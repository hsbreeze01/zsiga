# Spec: Feedback Loop Dashboard Section Rendering

## ADDED Requirements

### Requirement: _render_feedback_loop_section function

The system SHALL provide a function `_render_feedback_loop_section` in `zsiga/metrics/dashboard.py` that accepts a feedback loop metrics dict and returns an HTML string containing the "Feedback Loop" section.

The section SHALL contain 4 metric cards arranged in a grid:
1. **Learnings Health** — showing total count and top pattern distribution
2. **Learning Injection Rate** — showing injection rate per phase
3. **Auto-Proposal Success Rate** — showing success rate percentage and stuck count
4. **Self-Assessment Coverage** — showing coverage percentage

Each card SHALL use the existing `.card` CSS class from the dashboard stylesheet.

#### Scenario: Renders section with "No data yet" when metrics are zero

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::_render_feedback_loop_section
- **Given** a feedback loop metrics dict where all counts are zero (empty data state)
- **When** `_render_feedback_loop_section(metrics)` is called
- **Then** the returned HTML string SHALL contain the text "No data yet" and SHALL contain the substring "Feedback Loop"

#### Scenario: Renders metric values when data is present

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::_render_feedback_loop_section
- **Given** a feedback loop metrics dict with `learnings_health.total_count` = 42, `auto_proposal_success.success_rate_pct` = 75.0, `self_assessment_coverage.coverage_pct` = 60.0
- **When** `_render_feedback_loop_section(metrics)` is called
- **Then** the returned HTML SHALL contain "42" and "75.0%" and "60.0%" and SHALL NOT contain "No data yet"

### Requirement: Section positioning in dashboard

The "Feedback Loop" section SHALL appear in the rendered dashboard HTML BEFORE the "Recent Changes" section and AFTER the "Evolution Roadmap" section.

#### Scenario: Feedback Loop section precedes Recent Changes

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::_render
- **Given** the dashboard is being rendered with default data
- **When** `_render(stats, milestones, "resting")` is called
- **Then** in the returned HTML string, the substring "Feedback Loop" SHALL appear before the substring "Recent Changes"

### Requirement: Feedback Loop metrics dict injected into render

The `generate_dashboard` function or `_render` function SHALL call `collect_feedback_loop_metrics` to obtain the metrics data and pass it to `_render_feedback_loop_section`, integrating the resulting HTML into the dashboard output.

#### Scenario: generate_dashboard includes Feedback Loop section

- **testable**: true
- **target**: zsiga/metrics/dashboard.py::generate_dashboard
- **Given** the dashboard is being generated (writing to a temp path)
- **When** `generate_dashboard(output_path=tmp_output)` is called
- **Then** the written HTML file SHALL contain the substring "Feedback Loop"
