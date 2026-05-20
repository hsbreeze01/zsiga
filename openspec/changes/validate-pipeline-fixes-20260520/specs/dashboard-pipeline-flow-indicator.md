# Spec: dashboard-pipeline-flow-indicator

## ADDED Requirements

### Requirement: Dashboard page SHALL display a pipeline flow indicator below the title

The `site/dashboard.html` page SHALL render a single line of text immediately below the `<h1>` page title that displays the complete pipeline phase flow.

#### Scenario: Pipeline flow indicator text is visible on page load

- **Given** a user opens `site/dashboard.html` in a browser
- **When** the page finishes loading
- **Then** text reading `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER` SHALL be visible directly below the main heading
- **And** the text SHALL use arrow characters (`→`) to separate each phase name
- **And** the phase names SHALL appear in the exact order listed above

#### Scenario: Pipeline flow indicator styling is consistent with page design

- **Given** the dashboard dark theme uses `#94a3b8` for secondary text and `#334155` for subtle borders
- **When** the pipeline flow indicator is rendered
- **Then** the text SHALL use a subdued color consistent with existing secondary text (e.g., `#64748b` or `#94a3b8`)
- **And** the font size SHALL be noticeably smaller than the `<h1>` heading (e.g., `0.85rem` or similar)
- **And** the indicator SHALL NOT disrupt the existing page layout or spacing of adjacent elements

#### Scenario: Pipeline flow indicator is static HTML

- **Given** the pipeline flow indicator content is a fixed string
- **Then** the indicator SHALL be implemented as static HTML (not dynamically fetched via JavaScript)
- **And** the indicator SHALL NOT depend on any API call or external data source
