# add-proposal-stats-to-dashboard

## Summary
Add `GET /api/proposal-stats` endpoint to `zsiga/daemon.py` that returns JSON aggregate statistics from the `changes` SQLite table.

## Problem
The zsiga dashboard at `http://0.0.0.0:58175` shows daemon status (`/api/status`) and uptime, but has zero visibility into proposal pipeline health. Operators must SSH to the server and run raw SQL to understand:
- How many proposals succeeded vs failed
- What the average proposal duration is
- Which proposals are currently in-flight

This is a gap in operational observability for an autonomous system.

## Technical Design
Modify single file: `zsiga/daemon.py`

1. Add function `_build_proposal_stats_json(db_path: str) -> dict` that queries `changes` table:
   - `total`: `SELECT COUNT(*) FROM changes`
   - `by_outcome`: `SELECT outcome, COUNT(*) FROM changes GROUP BY outcome`
   - `avg_duration_seconds`: `SELECT AVG(julianday(finished_at) - julianday(started_at)) * 86400 FROM changes WHERE finished_at IS NOT NULL`
   - `recent`: `SELECT change_name, outcome, started_at, finished_at FROM changes ORDER BY id DESC LIMIT 5`

2. Add `/api/proposal-stats` route in the existing HTTP handler (same pattern as `/api/status`)

3. Return JSON: `{"total": N, "by_outcome": {...}, "avg_duration_seconds": X, "recent": [...]}`

## Acceptance Criteria
- `curl http://localhost:58175/api/proposal-stats` returns HTTP 200 with valid JSON
- JSON contains keys: `total`, `by_outcome`, `avg_duration_seconds`, `recent`
- Existing endpoints (`/api/status`, `/`) unchanged and functional
- No new pip dependencies — uses only `sqlite3` (stdlib)

## Scope
- **In scope**: Single endpoint in `zsiga/daemon.py`, read-only queries
- **Out of scope**: UI dashboard rendering, historical charts, WebSocket streaming

## Risk
- **Impact**: Very low — read-only, no state mutation
- **Blast radius**: Single endpoint; if broken, returns 500 but does not affect daemon operation
- **Reversibility**: Delete the route and function
