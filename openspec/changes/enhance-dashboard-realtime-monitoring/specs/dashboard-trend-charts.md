# Delta Spec: Dashboard Rolling Trend Charts

## ADDED Requirements

### Requirement: Success Rate Sparkline

The dashboard generator SHALL render a Success Rate Sparkline visualizing the rolling success rate of the most recent 20 changes. The sparkline MUST be implemented using pure CSS `<div>` elements (no external JS libraries). The data SHALL be sourced from `metrics/collector.py`'s `compute_rolling_rates` function.

Each bar in the sparkline SHALL be color-coded:
- **Green** (`#22c55e`): success
- **Red** (`#ef4444`): failure
- **Yellow** (`#f59e0b`): timeout / unknown outcome

The section SHALL include a numeric label showing the current rolling success rate percentage.

#### Scenario: 20 changes exist with mixed outcomes

- **Given** `data/changes.json` contains at least 20 changes with various outcomes
- **When** the dashboard HTML is generated
- **Then** the sparkline SHALL render 20 bars, each colored by outcome
- **And** a percentage label SHALL display the rolling success rate

#### Scenario: Fewer than 20 changes exist

- **Given** `data/changes.json` contains only 5 changes
- **When** the dashboard HTML is generated
- **Then** the sparkline SHALL render 5 bars corresponding to those changes
- **And** the percentage label SHALL reflect the success rate of those 5 changes

### Requirement: Duration Trend Bar Chart

The dashboard generator SHALL render a Duration Trend Bar Chart visualizing the processing duration of the most recent 20 changes. Each bar's height SHALL be proportional to the duration (computed from `started_at` / `finished_at` fields). The chart MUST be implemented using pure CSS `<div>` elements.

Each bar SHALL be color-coded matching its outcome:
- **Green**: success
- **Red**: failure / reverted
- **Yellow**: timeout

The section SHALL include a tooltip-style label (via CSS `title` attribute) on each bar showing the change name and duration.

#### Scenario: Changes with duration data

- **Given** `data/changes.json` contains changes with valid `started_at` and `finished_at` fields
- **When** the dashboard HTML is generated
- **Then** the chart SHALL render proportional bars with correct colors
- **And** each bar SHALL have a `title` attribute with change name and formatted duration

#### Scenario: Change missing duration fields

- **Given** a change entry lacks `started_at` or `finished_at`
- **When** the dashboard HTML is generated
- **Then** that change SHALL be skipped in the duration chart without causing an error
