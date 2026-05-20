# Tasks: Dashboard Proposal Queue Panel

## 1. Proposal Queue Scanning & Rendering

- [ ] **Add `_render_proposal_queue()` function** in `zsiga/metrics/dashboard.py`: load config targets, create transports, run `DirectoryScanner.scan()`, read first heading line of each `proposal.md` via transport, load daemon_state.json for current_change/current_phase matching, render HTML table with highlight row and phase badge, handle empty queue ("Queue empty — idle polling"), wrap in try/except for resilience
- [ ] **Integrate queue section into `_render()` template** in `zsiga/metrics/dashboard.py`: call `_render_proposal_queue()` between daemon_section and Phase Performance, insert `{proposal_queue_section}` placeholder in the HTML template string at the correct position

## 2. Testing

- [ ] **Add unit tests for `_render_proposal_queue()`** in `tests/test_dashboard_queue.py`: test empty queue rendering, test multi-proposal table with correct columns, test current-change highlight when daemon_state has active change, test proposal summary extraction from first heading line, test missing proposal.md fallback
