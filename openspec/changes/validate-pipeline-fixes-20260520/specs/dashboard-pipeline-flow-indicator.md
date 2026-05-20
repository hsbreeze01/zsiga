# Delta Spec: Dashboard Pipeline Flow Indicator

## ADDED Requirements

### Requirement: Pipeline Flow Indicator Line

The dashboard HTML page (`site/dashboard.html`) SHALL display a single line of descriptive text immediately below the main heading (`<h1>`). This line MUST show the full pipeline stage sequence in order:

```
CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER
```

#### Scenario: Indicator visible on page load

- **Given** a user opens `site/dashboard.html` in a browser
- **When** the page finishes loading
- **Then** a line of text SHALL appear directly below the `<h1>` heading
- **And** the text SHALL read `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
- **And** the text SHALL use a subdued (gray) color consistent with existing auxiliary labels (e.g. `#64748b` or `#94a3b8`)
- **And** the text font size SHALL be smaller than the heading (`<h1>`)

#### Scenario: Layout preservation

- **Given** the existing dashboard layout before this change
- **When** the indicator line is added
- **Then** no existing UI elements SHALL be displaced, hidden, or resized
- **And** the existing card grid, tables, milestone sections, and journal entries SHALL render identically

#### Scenario: Stage sequence ordering

- **Given** the pipeline flow indicator text
- **When** rendered
- **Then** the stages SHALL appear in this exact left-to-right order: CLARIFY, ENRICH, IMPLEMENT, REVIEW, VERIFY, OPTIMIZE, REFLECT, DELIVER
- **And** each adjacent pair SHALL be separated by the `→` character

#### Scenario: Static content only

- **Given** the pipeline flow indicator text
- **When** the HTML source is inspected
- **Then** the text SHALL be a static string (no JavaScript or dynamic template required)
- **Note** This means future pipeline stage name changes will require manual HTML update, which is an accepted trade-off per the clarify boundary
