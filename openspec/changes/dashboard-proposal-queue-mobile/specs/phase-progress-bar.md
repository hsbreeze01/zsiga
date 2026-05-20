# Spec: Phase Progress Bar

## ADDED Requirements

### Requirement: Eight-Phase Progress Bar

The dashboard SHALL render a horizontal progress bar showing the eight daemon phases in order: CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER. Each phase step SHALL visually indicate its status: completed (green), current (highlighted), or future (grey).

#### Scenario: Daemon is mid-pipeline (e.g., in REVIEW phase)

- **Given** `daemon_state.json` contains `current_phase` set to `"REVIEW"`
- **When** the dashboard HTML is generated
- **Then** the progress bar SHALL render 8 phase steps
- **And** phases CLARIFY, ENRICH, IMPLEMENT, REVIEW SHALL appear with completed/highlighted styling
- **And** phases VERIFY, OPTIMIZE, REFLECT, DELIVER SHALL appear with future (grey) styling
- **And** the REVIEW phase step SHALL be visually distinct as the current phase (highlighted)

#### Scenario: Daemon is idle (no current phase)

- **Given** `daemon_state.json` does not exist or `current_phase` is empty/null
- **When** the dashboard HTML is generated
- **Then** the progress bar SHALL render all 8 phase steps with future (grey) styling
- **And** no phase step SHALL be marked as current or completed

#### Scenario: All 8 phase names present in HTML

- **Given** any dashboard generation invocation
- **When** the output HTML is inspected
- **Then** each of the 8 phase names (CLARIFY, ENRICH, IMPLEMENT, REVIEW, VERIFY, OPTIMIZE, REFLECT, DELIVER) SHALL appear as text content within the progress bar HTML structure

### Requirement: Progress Bar Mobile Scrollability

The phase progress bar SHALL be horizontally scrollable on narrow viewports so that all 8 phase names remain accessible without layout breakage.

#### Scenario: Progress bar on narrow viewport

- **Given** a viewport width of 375px (typical mobile)
- **When** the progress bar is rendered
- **Then** the progress bar container SHALL allow horizontal scrolling (`overflow-x: auto`)
- **And** all 8 phase steps SHALL remain readable without clipping
