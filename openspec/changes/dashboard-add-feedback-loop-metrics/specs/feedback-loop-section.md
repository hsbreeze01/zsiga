# Spec: Feedback Loop Dashboard Section

## ADDED Requirements

### Requirement: Feedback Loop section in dashboard HTML

The `_render()` function in `zsiga/metrics/dashboard.py` SHALL include a "Feedback Loop" metrics section rendered as HTML, positioned **before** the "Recent Changes" section and **after** the "Failure Diagnosis" section.

The section SHALL use the existing `.section` and `.grid` CSS classes for visual consistency.

#### Scenario: Dashboard HTML contains Feedback Loop section

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated via `generate_dashboard()`
- **When** the output HTML is inspected
- **Then** it SHALL contain a `<div class="section">` element with an `<h2>` containing the text "Feedback Loop"

#### Scenario: Feedback Loop section positioned before Recent Changes

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated
- **When** the output HTML is inspected
- **Then** the "Feedback Loop" section SHALL appear before the "Recent Changes" section in the HTML string

### Requirement: Four metric cards rendered

The Feedback Loop section SHALL contain four cards, each displaying one of the four feedback-loop metrics. Each card SHALL use the `.card` CSS class and show a label and value.

#### Scenario: Learnings Health card rendered

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated
- **When** the output HTML is inspected
- **Then** it SHALL contain a card with a label containing "Learnings Health" and a value showing the total learnings count or "No learnings yet" when total is 0

#### Scenario: Auto-Proposal Success card rendered

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated
- **When** the output HTML is inspected
- **Then** it SHALL contain a card with a label containing "Auto-Proposal Success" and a value showing the success rate percentage or "No auto-proposals yet" when total is 0

#### Scenario: Self-Assessment Coverage card rendered

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated
- **When** the output HTML is inspected
- **Then** it SHALL contain a card with a label containing "Self-Assessment Coverage" and a value showing the coverage percentage or "No self-assessments yet" when assessed_changes is 0

#### Scenario: Injection Rate card rendered

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated
- **When** the output HTML is inspected
- **Then** it SHALL contain a card with a label containing "Injection Rate" and a value showing the implement injection rate or "No data yet" when no implement phases exist

### Requirement: Graceful empty-data degradation

When metrics data is unavailable (empty database, missing tables, or compute errors), the dashboard SHALL still render successfully with placeholder text instead of numeric values.

#### Scenario: Dashboard renders with all "No data yet" placeholders on empty DB

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** a completely empty metrics database
- **When** `generate_dashboard()` is called
- **Then** the HTML SHALL contain "No learnings yet", "No data yet", "No auto-proposals yet", and "No self-assessments yet" in their respective card areas, and no exceptions SHALL be raised

### Requirement: Non-breaking insertion

The new Feedback Loop section SHALL NOT alter the structure or content of any existing dashboard sections. All existing sections (Phase Performance, Failure Diagnosis, Evolution Roadmap, Recent Changes, etc.) SHALL render exactly as before.

#### Scenario: Existing sections unchanged after adding Feedback Loop

- **testable**: true
- **target**: zsiga.metrics.dashboard.generate_dashboard
- **Given** the dashboard is generated with the Feedback Loop section added
- **When** the output HTML is inspected
- **Then** the HTML SHALL still contain "Phase Performance", "Failure Diagnosis", "Evolution Roadmap", and "Recent Changes" sections

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
