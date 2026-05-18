# Phase Duration Histogram

## ADDED Requirements

### Requirement: Phase Duration Statistics with Min/Max

The metrics collector SHALL compute per-phase duration statistics including average, min, and max `seconds_used` across all recorded phase executions.

#### Scenario: Computing phase duration stats with multiple phase records

- Given 3 implement phase records with `seconds_used` values of 100.0, 200.0, and 300.0
- When `compute_stats()` is called
- Then the `phase_stats["implement"]` dict SHALL contain keys `avg_seconds` (200.0), `min_seconds` (100.0), and `max_seconds` (300.0)
- And the values SHALL be rounded to 1 decimal place

#### Scenario: Phase with zero records

- Given no phase records for "deliver"
- When `compute_stats()` is called
- Then `phase_stats["deliver"]` SHALL contain only `{"count": 0}` with no `min_seconds` or `max_seconds` keys

#### Scenario: Phase with a single record

- Given exactly 1 verify phase record with `seconds_used` of 81.9
- When `compute_stats()` is called
- Then `phase_stats["verify"]["min_seconds"]` SHALL equal `phase_stats["verify"]["max_seconds"]` which SHALL equal 81.9

---

### Requirement: Horizontal Bar Chart Visualization

The dashboard SHALL render a horizontal bar chart section titled "Phase Duration" showing one bar per pipeline phase (enrich, implement, verify, deliver), color-coded by phase, with min/max range indicators.

#### Scenario: Rendering bars for phases with data

- Given `phase_stats` containing all 4 phases with non-zero counts
- When the dashboard is generated
- Then a section with heading "Phase Duration" SHALL appear after the "Phase Performance" table
- And each phase SHALL display as a horizontal bar whose length represents `avg_seconds`
- And each bar SHALL show a min/max range indicator (a lighter-colored range line extending from min to max)
- And each bar row SHALL display the phase name, average time, and min–max label (e.g. "148.9s avg · 45.2s–312.0s range")

#### Scenario: Color coding per phase

- Given the dashboard is generated
- Then the "enrich" phase bar SHALL use color `#06b6d4` (cyan)
- And the "implement" phase bar SHALL use color `#8b5cf6` (violet)
- And the "verify" phase bar SHALL use color `#f59e0b` (amber)
- And the "deliver" phase bar SHALL use color `#22c55e` (green)

#### Scenario: Phases with zero count

- Given `phase_stats["deliver"]["count"]` is 0
- When the dashboard is generated
- Then the "deliver" row SHALL still appear in the chart
- And its bar SHALL have zero width with text "No data"

#### Scenario: Chart uses pure CSS, no JavaScript

- Given the generated dashboard HTML
- Then the histogram SHALL be rendered using only HTML `<div>` elements and CSS
- And there SHALL be no `<script>` tags or JavaScript for the chart rendering
- And the chart SHALL follow the existing dark-theme CSS variables (`#1e293b`, `#334155`, etc.)
