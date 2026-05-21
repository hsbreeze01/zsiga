# Spec: Mobile Responsiveness

## ADDED Requirements

### Requirement: Responsive Layout at Narrow Viewports

The dashboard SHALL include a `@media (max-width: 768px)` CSS block that adapts the page layout for mobile devices. All critical content SHALL remain readable and usable without horizontal overflow at viewport widths down to 320px.

#### Scenario: Viewing dashboard on a mobile phone (375px wide)

- **Given** the generated dashboard HTML
- **When** the page is rendered in a viewport 375px wide
- **Then** the body padding SHALL be reduced to 1rem
- **And** the `.grid` card layout SHALL switch to a single column (`grid-template-columns: 1fr`)
- **And** the `h1` heading font size SHALL be reduced to at most 1.2rem
- **And** the `.hero` section SHALL stack vertically (`flex-direction: column`)
- **And** table cells (`th`, `td`) SHALL have reduced padding (≤0.6rem)
- **And** `.card .value` font size SHALL be reduced for mobile readability

#### Scenario: Media query present in generated CSS

- **Given** any dashboard generation invocation
- **When** the output HTML `<style>` block is inspected
- **Then** the string `@media (max-width: 768px)` SHALL appear exactly once
- **And** the media block SHALL contain rules for at least: `body`, `.grid`, `h1`, `.hero`, `table`, `th`/`td`

#### Scenario: Desktop layout unchanged

- **Given** the generated dashboard HTML
- **When** the page is rendered in a viewport wider than 768px
- **Then** all layout rules SHALL behave as before the mobile adaptation
- **And** the `@media` block SHALL NOT affect desktop rendering

### Requirement: No Desktop Regression

The mobile adaptation SHALL NOT alter the visual appearance or behavior of the dashboard at viewport widths above 768px.

#### Scenario: Desktop viewport after mobile styles added

- **Given** the generated dashboard HTML with the new `@media` block
- **When** rendered at 1440px width
- **Then** the layout, fonts, spacing, and colors SHALL match the pre-change desktop appearance exactly
