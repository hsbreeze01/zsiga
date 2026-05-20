# Delta Spec: Dashboard Pipeline Flow Indicator

## Context
The dashboard page (`site/dashboard.html`) currently shows the project title but does not communicate the full pipeline process. Adding a pipeline flow indicator makes the 8-stage process visible and confirms the dashboard frontend is being updated alongside backend changes.

## ADDED Requirements

### Requirement: Pipeline flow text SHALL appear below the page title

A single line of text SHALL be rendered immediately below the `<h1>` heading in `site/dashboard.html`, displaying the complete pipeline flow in order:

`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`

#### Scenario: Text is visible on page load
- **Given** a user opens `site/dashboard.html` in a browser
- **When** the page finishes loading
- **Then** the pipeline flow text SHALL be visible directly below the main heading
- **And** the text SHALL read exactly `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`

#### Scenario: Text style is subdued and non-intrusive
- **Given** the pipeline flow text is rendered
- **When** a user views the page
- **Then** the text SHALL use a smaller font size than the `<h1>` heading
- **And** the text color SHALL be a muted tone consistent with the existing dashboard palette (e.g., `#64748b` or `#94a3b8`)
- **And** the text SHALL have appropriate spacing below the heading (at least `0.3rem`)

### Requirement: Pipeline indicator MUST NOT break existing layout

The new text element SHALL be inserted inline within the existing title area and MUST NOT alter the positioning, styling, or functionality of any other dashboard component.

#### Scenario: Existing cards and sections remain unaffected
- **Given** the pipeline flow text has been added
- **When** the dashboard renders
- **Then** all stat cards, milestone sections, and journal entries SHALL retain their original layout and styling

#### Scenario: Mobile viewport compatibility
- **Given** the dashboard is viewed on a viewport narrower than 600px
- **When** the pipeline flow text is rendered
- **Then** the text SHALL wrap naturally without causing horizontal overflow
- **And** no other elements SHALL be displaced

## MODIFIED Requirements

_(None)_

## REMOVED Requirements

_(None)_
