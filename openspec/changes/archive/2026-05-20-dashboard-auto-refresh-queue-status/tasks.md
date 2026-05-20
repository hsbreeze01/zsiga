# Tasks: Dashboard Auto-Refresh & Queue/Stage Real-Time Display

## 1. Backend API

- [x] **1.1 Add `/api/status.json` endpoint to daemon HTTP handler** — Add a route in the daemon's HTTP request handler that responds to `GET /api/status.json` with a JSON payload containing `daemon` state (from `daemon_state.json`) and `queue` (from scanning `openspec/changes/*/proposal.md`). Include safe defaults when `daemon_state.json` is missing or malformed. Return `Content-Type: application/json`.

- [x] **1.2 Add queue scanning helper function** — Create a helper (e.g., `_scan_proposal_queue(changes_dir)`) that walks `openspec/changes/`, reads each `proposal.md`, extracts the first `# ` heading as summary, and returns a list of `{name, project, summary}` dicts. Keep it under the existing module's conventions.

## 2. Dashboard Template Update

- [x] **2.1 Remove `<meta http-equiv="refresh">` and inject JS polling script** — In the HTML template in `zsiga/metrics/dashboard.py`, remove the `<meta http-equiv="refresh" content="60">` tag. Add a `<script>` block at end of `<body>` that uses `setInterval` to `fetch('/api/status.json')` every 600 seconds and updates the daemon status card, proposal queue table, and refresh timestamp in the DOM. Include `try/catch` for graceful fallback to static content on fetch failure.

- [x] **2.2 Add dynamic proposal queue section to HTML template** — In the dashboard template, add a `<div id="queue-section">` containing a table placeholder. The JS from task 2.1 will populate this table on each fetch with columns: index, name, project, summary. The active proposal row gets a highlight class and phase badge. When queue is empty, show "Queue empty — idle polling".

- [x] **2.3 Add refresh timestamp and countdown indicator** — Add a `<span id="refresh-info">` element in the top-right area of the dashboard. JS updates it with "Last refreshed: HH:MM:SS" and a minute countdown to the next fetch cycle.

## 3. Phase State Update Timing

- [ ] **3.1 Ensure daemon writes `current_phase` before phase execution** — Verify and, if needed, adjust the daemon's phase transition logic so that `daemon_state.json` is updated with the new `current_change` and `current_phase` *before* the phase's main logic runs, not after. This ensures `/api/status.json` always reflects the active phase.

## 4. Testing

- [x] **4.1 Add tests for `/api/status.json` endpoint** — Test the new API route: (a) returns valid JSON with expected structure, (b) returns defaults when `daemon_state.json` missing, (c) queue reflects actual `openspec/changes/` contents. Place tests in `tests/test_dashboard_queue.py` or a new `tests/test_dashboard_api.py`.

- [ ] **4.2 Verify existing dashboard tests still pass** — Run full pytest suite to confirm no regressions in `tests/test_dashboard_queue.py` or other test files.
