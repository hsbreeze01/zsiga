# Delta Spec: Phase Progress Bar Visual Component

## ADDED Requirements

### REQ-PHASE-001: Eight-Stage Phase Progress Bar

The dashboard SHALL render a visual phase progress bar showing the eight OpenSpec pipeline stages with distinct visual states.

#### Scenario: Progress bar renders with correct stage labels
- **Given** the dashboard renders the Current sub-section
- **When** the phase progress bar is generated
- **Then** it SHALL display eight stages in order: CLARIFY, ENRICH, IMPLEMENT, REVIEW, VERIFY, OPTIMIZE, REFLECT, DELIVER
- **And** each stage SHALL be a discrete visual element with a text label

#### Scenario: Completed phases are visually distinct
- **Given** the daemon's `current_phase` is `VERIFY` (index 4, 0-based)
- **When** the progress bar is rendered
- **Then** stages CLARIFY, ENRICH, IMPLEMENT, REVIEW (indices 0–3) SHALL be styled as "completed" (green)
- **And** stage VERIFY (index 4) SHALL be styled as "current" (highlighted)
- **And** stages OPTIMIZE, REFLECT, DELIVER (indices 5–7) SHALL be styled as "pending" (grey)

#### Scenario: Phase value is unrecognized or missing
- **Given** the daemon's `current_phase` value does not match any known stage name (case-insensitive)
- **When** the progress bar is rendered
- **Then** all stages SHALL be rendered in pending (grey) state
- **And** no error SHALL be raised

#### Scenario: Phase value is DELIVER (final stage)
- **Given** the daemon's `current_phase` is `DELIVER` (index 7)
- **When** the progress bar is rendered
- **Then** stages CLARIFY through OPTIMIZE (indices 0–6) SHALL be styled as "completed"
- **And** stage DELIVER (index 7) SHALL be styled as "current"

---

### REQ-PHASE-002: Phase Progress Bar CSS Styles

The dashboard `<style>` block SHALL include CSS classes for phase progress bar states.

#### Scenario: CSS defines three visual states
- **Given** the dashboard HTML output
- **When** inspecting the `<style>` block
- **Then** there SHALL be a CSS class for "completed" phase state (green color)
- **And** there SHALL be a CSS class for "current" phase state (highlighted/distinct color)
- **And** there SHALL be a CSS class for "pending" phase state (grey color)
- **And** a `.phase-progress` class SHALL exist for the container element
