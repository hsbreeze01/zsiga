# Design: Dashboard 实时监控与异常诊断增强

## Architecture Decisions

### ADR-1: Daemon state via JSON file (not HTTP endpoint)
**Decision**: Daemon writes `data/daemon_state.json` on every phase transition.
**Rationale**: zsiga dashboard is a static HTML generator — it reads data files and produces HTML. There is no running web server to serve dynamic API endpoints. A JSON file on disk is the simplest mechanism consistent with the existing architecture. The dashboard generator reads this file at render time.

### ADR-2: Pure CSS charts (no JS chart libraries)
**Decision**: All trend visualizations use CSS `<div>` bars with inline `width`/`height`/`background-color` styles.
**Rationale**: The project constraint explicitly forbids external JS libraries. CSS div-based sparklines and bar charts are sufficient for 20-data-point visualizations and require zero dependencies.

### ADR-3: Failure diagnosis sourced from learnings.jsonl
**Decision**: Error summaries are extracted by matching change name + phase in `memory/learnings.jsonl` entries.
**Rationale**: learnings.jsonl already captures failure context as lessons. Reusing this data avoids duplicating error storage. The matching logic uses substring search on the lesson text for the change name.

### ADR-4: Auto-refresh via meta tag (not JavaScript)
**Decision**: Use `<meta http-equiv="refresh" content="60">` for page reload.
**Rationale**: Simplest possible implementation. No JS required. The daemon already re-renders the dashboard periodically, so a 60-second reload interval ensures the user sees fresh data without any complexity.

## Data Flow

```
daemon.py (daemon_loop)
  │  on every phase transition
  ▼
data/daemon_state.json
  │
  ▼
dashboard.py (_render_daemon_card)
  │
  ▼
site/dashboard.html  (daemon status card section)


data/changes.json ──┐
memory/learnings.jsonl ──┤
metrics/collector.py ────┤
                    ▼
dashboard.py
  ├── _render_failure_panel()   →  failure diagnosis section
  ├── _render_trend_charts()    →  rolling trend section
  └── _inject_auto_refresh()    →  meta tag + indicator
                    │
                    ▼
          site/dashboard.html
```

## Files to Add / Modify

### Modified Files

| File | Change Description |
|------|-------------------|
| `zsiga/daemon.py` | Add `_write_daemon_state()` helper; call it on phase transitions in `daemon_loop`. Write `data/daemon_state.json` with pid, started_at, cycle, state, current_change, current_phase, current_project, last_heartbeat. |
| `zsiga/dashboard.py` | Add 4 new rendering functions: `_render_daemon_card()`, `_render_failure_panel()`, `_render_trend_charts()`, `_inject_auto_refresh()`. Call them in the main HTML generation pipeline. Add CSS styles for new sections. |
| `site/dashboard.html` | Regenerated output (no manual edits). |

### New Files

| File | Change Description |
|------|-------------------|
| `tests/test_daemon_state.py` | Test daemon state file writing: correct fields, idle state, missing file handling. |
| `tests/test_dashboard_failure_panel.py` | Test failure panel rendering: with failures, without failures, matching lessons, truncation at 10. |
| `tests/test_dashboard_trends.py` | Test trend chart data preparation: success rate calculation, duration extraction, missing data handling. |

## CSS Classes Added to Dashboard

New classes for daemon card, failure panel, and trend charts will follow the existing naming convention (kebab-case, consistent with `.card`, `.milestone`, `.section`, etc.):

- `.daemon-card` — container for daemon status info
- `.daemon-field` — individual field row (label + value)
- `.failure-entry` — single failure row
- `.failure-detail` — expandable details block
- `.trend-section` — wrapper for trend charts
- `.sparkline` — success rate sparkline container
- `.sparkline-bar` — individual bar in sparkline
- `.duration-chart` — duration bar chart container
- `.duration-bar` — individual bar in duration chart
- `.auto-refresh-badge` — the "Auto-refresh: 60s" indicator

## Rendering Pipeline (in dashboard.py)

The existing dashboard generation flow is extended:

1. `_inject_auto_refresh()` — adds meta tag to `<head>` and badge to header
2. `_render_hero()` — existing, unchanged
3. **`_render_daemon_card()`** — NEW, inserted here
4. `_render_metric_cards()` — existing metric grid
5. `_render_phase_performance()` — existing table
6. **`_render_failure_panel()`** — NEW, inserted here
7. **`_render_trend_charts()`** — NEW, inserted here
8. `_render_milestones()` — existing milestones
9. `_render_journal()` — existing journal

## Error Handling

- If `data/daemon_state.json` is missing or malformed, `_render_daemon_card()` returns a "Daemon Offline" card — dashboard never crashes.
- If `memory/learnings.jsonl` is missing, `_render_failure_panel()` shows failures without error context.
- If `data/changes.json` has entries with missing `started_at`/`finished_at`, `_render_trend_charts()` skips those entries gracefully.
- All file reads use `try/except` with sensible defaults, matching the existing pattern in `dashboard.py`.
