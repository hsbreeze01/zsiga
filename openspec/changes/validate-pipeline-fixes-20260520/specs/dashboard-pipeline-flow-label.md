# Spec: dashboard-pipeline-flow-label

## ADDED Requirements

### Requirement: Dashboard title area SHALL display the full pipeline flow

The `site/dashboard.html` page SHALL show a single line of small descriptive
text directly beneath the existing `<h1>` heading element.  The text SHALL read:

```
CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER
```

#### Scenario: pipeline flow line visible on page load

- **Given** a browser loads `site/dashboard.html`
- **When** the page finishes rendering
- **Then** the text `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER` SHALL be visible immediately below the `<h1>` heading
- **And** the text styling SHALL be consistent with the existing `.meta` class
  (small, muted color)

#### Scenario: flow line does not duplicate on repeated renders

- **Given** the dashboard page is loaded once
- **When** any client-side JavaScript runs
- **Then** there SHALL be exactly one pipeline flow line in the DOM
- **And** no duplicate lines SHALL be injected

### Requirement: Pipeline flow label MUST NOT alter existing page structure

The new line MUST be inserted as a sibling element immediately after the `<h1>`
tag, without re-parenting, removing, or otherwise modifying any existing
elements.

#### Scenario: existing hero section unchanged

- **Given** the dashboard page HTML structure before the change
- **When** the pipeline flow line is inserted
- **Then** all existing child elements of the hero / header section SHALL remain
  in the same order and with the same attributes
