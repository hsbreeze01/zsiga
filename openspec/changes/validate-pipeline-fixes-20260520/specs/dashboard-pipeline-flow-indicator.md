# Spec: Dashboard Pipeline Flow Indicator

## ADDED Requirements

### Requirement: Dashboard title area SHALL display pipeline flow indicator

The `site/dashboard.html` page SHALL render a single line of muted text directly below the main heading (`<h1>`), showing the complete pipeline phase sequence: `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`.

#### Scenario: Pipeline flow indicator is visible on page load

- **Given** the dashboard HTML page is loaded in a browser
- **When** the page finishes rendering
- **Then** a line of text SHALL be visible directly below the `<h1>` heading
- **And** the text SHALL read exactly `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
- **And** the text SHALL use a muted/subtle color (e.g. `#64748b`) and a small font size (e.g. `0.8rem`)

#### Scenario: Pipeline flow indicator uses static HTML

- **Given** the dashboard page source
- **When** inspecting the HTML
- **Then** the pipeline flow indicator text SHALL be hardcoded in the HTML template
- **And** it SHALL NOT depend on JavaScript rendering or API calls
- **And** it SHALL NOT change based on runtime state

### Requirement: Pipeline flow indicator MUST NOT alter existing layout

The addition of the pipeline flow indicator line MUST NOT shift, overlap, or obscure any existing dashboard elements above or below it.

#### Scenario: Existing cards and tables remain in place

- **Given** the dashboard page with the new pipeline flow indicator
- **When** viewing the hero section and metric cards
- **Then** all existing elements (state badge, mascot, metric cards, tables) SHALL render in the same positions and sizes as before
- **And** there SHALL be no layout breakage or visual regression
