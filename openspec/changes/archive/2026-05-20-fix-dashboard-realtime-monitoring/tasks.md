# Tasks: Fix Dashboard Realtime Monitoring

## 1. Daemon Status Card (P1)

- [ ] Add `_render_daemon_status()` function to dashboard.py that reads `data/daemon_state.json`, handles missing/corrupt file gracefully, and returns HTML for a daemon status card row (PID, Started At, Cycle, State badge, Processing info, Heartbeat)
- [ ] Wire `_render_daemon_status()` into `_render()` — insert its output between the hero section and the metrics card grid

## 2. Failure Diagnosis Panel (P2)

- [ ] Add `_render_failure_diagnosis()` function that scans change directories for reverted/failed outcomes, matches lessons from `learnings.jsonl`, checks for `diagnosis.md`, and returns HTML `<details>/<summary>` list of up to 10 recent failures
- [ ] Wire `_render_failure_diagnosis()` into `_render()` — insert between Phase Performance table and Resource Usage section

## 3. Sparkline & Duration Trends (P3)

- [ ] Add success trend and duration trend rendering in `_render()` — call `compute_rolling_rates` + `_sparkline_html` for the success sparkline card, and generate pure-CSS bar chart for duration trend (color-coded green/red, height as percentage of max)
- [ ] Insert both trend cards into the Resource Usage area of the HTML output in `_render()`

## 4. Auto-Refresh (P4)

- [ ] Add `<meta http-equiv="refresh" content="60">` to the `<head>` section and a centered muted "Auto-refresh: 60s" hint line at the top of `<body>` in the `_render()` HTML template

## 5. Verification

- [ ] Run `ruff check` on modified files and fix any lint issues
- [ ] Run `pytest` to ensure no regressions
