# Delta Spec: Mobile Responsiveness & JS Cleanup

## ADDED Requirements

### REQ-MOBILE-001: Mobile Viewport Adaptation

The dashboard page SHALL include CSS `@media` rules that adapt layout for viewports ≤768px wide.

#### Scenario: Dashboard viewed on mobile device (≤768px)
- **Given** the dashboard HTML is loaded in a browser
- **When** the viewport width is 768px or less
- **Then** the following layout changes SHALL apply:
  - `body` padding reduces to `1rem`
  - `.grid` cards display in a single column (`grid-template-columns: 1fr`)
  - `h1` heading font-size reduces to `1.2rem`
  - `.hero` container switches to vertical stacking (`flex-direction: column`) with `gap: 1rem`
  - `table` font-size reduces to `0.75rem`
  - `th, td` padding reduces to `0.4rem 0.6rem`
  - `.card .value` font-size reduces to `1.4rem`
  - `.phase-progress` container enables horizontal scrolling (`overflow-x: auto`)

#### Scenario: Dashboard viewed on desktop (>768px)
- **Given** the dashboard HTML is loaded in a browser
- **When** the viewport width is greater than 768px
- **Then** the existing desktop layout SHALL remain unchanged

---

### REQ-MOBILE-002: Phase Progress Bar Horizontal Scroll on Mobile

The eight-stage phase progress bar SHALL be horizontally scrollable on narrow viewports to prevent overflow or truncation.

#### Scenario: Phase progress bar overflows on narrow screen
- **Given** the Current sub-section is rendered with a phase progress bar
- **When** the viewport width is ≤768px and the progress bar exceeds the container width
- **Then** the `.phase-progress` container SHALL allow horizontal scrolling
- **And** all eight phase labels SHALL remain readable without truncation

---

## REMOVED Requirements

### REQ-LEGACY-001: JavaScript Dynamic Queue Rendering

The dashboard SHALL NOT include client-side JavaScript that fetches from `/api/status.json` or dynamically renders queue content.

#### Scenario: No stale JS fetch logic remains
- **Given** the generated dashboard HTML
- **When** inspecting the `<script>` block
- **Then** there SHALL be no `fetch('/api/status.json')` call
- **And** there SHALL be no `updateQueueSection` function definition
- **And** there SHALL be no `updateDaemonSection` function definition
- **And** there SHALL be no `<div id="queue-section">` element in the HTML

#### Scenario: Non-queue JavaScript is preserved
- **Given** the generated dashboard HTML
- **When** inspecting the `<script>` block
- **Then** the auto-refresh countdown timer and `updateRefreshInfo` logic SHALL still function
- **And** the page SHALL still update the refresh-info display in the top-right corner
