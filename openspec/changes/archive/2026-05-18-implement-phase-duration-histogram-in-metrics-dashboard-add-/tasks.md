# Tasks: Phase Duration Histogram

## Group 1: Backend Data Layer

- [ ] 1.1 Add min/max duration statistics to phase_stats computation in `zsiga/metrics/collector.py` — extend the `compute_stats()` phase aggregation loop to also compute `min_seconds` and `max_seconds` from `seconds_used` values for each phase, following the same pattern as `avg_seconds`

## Group 2: Dashboard Visualization

- [ ] 2.1 Add `_phase_histogram()` renderer function in `zsiga/metrics/dashboard.py` — a new function that takes `phase_stats` dict and returns an HTML section with a CSS-only horizontal bar chart showing 4 phases, each with a colored average-duration bar and a min/max range indicator, using the project's dark theme colors
- [ ] 2.2 Integrate histogram section into `_render()` and add histogram CSS — insert the `_phase_histogram()` call into the `_render()` function after the Phase Performance table section, and add the histogram-specific CSS classes (`.histogram`, `.hist-row`, `.hist-bar`, `.hist-range`) to the embedded `<style>` block
