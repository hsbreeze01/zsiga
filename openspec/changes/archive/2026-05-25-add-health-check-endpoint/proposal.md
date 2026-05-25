# add-health-check-endpoint

## Summary
Add a `GET /api/health` endpoint to `zsiga/daemon.py` that performs a lightweight liveness check on the daemon and database.

## Problem
The existing `/api/status` returns daemon metadata but does not verify that the system is actually functional. If the SQLite database is corrupted or locked, `/api/status` still returns 200. Operators need a true health check that confirms the daemon can read its own data.

## Technical Design
Modify single file: `zsiga/daemon.py`

1. Add function `_health_check(db_path: str) -> dict`:
   - Try `sqlite3.connect(db_path)` and `SELECT COUNT(*) FROM changes`
   - If connection fails or table missing, return `{"status": "unhealthy", "error": "..."}`
   - If successful, return `{"status": "healthy", "db_records": count}`

2. Add `/api/health` route in the existing HTTP handler (same pattern as `/api/proposal-stats`):
   - Calls `_health_check`
   - Returns HTTP 200 for healthy, HTTP 503 for unhealthy
   - Response: `{"status": "healthy"|"unhealthy", "db_records": N, "timestamp": "ISO8601"}`

## Acceptance Criteria
1. `curl http://localhost:58175/api/health` returns HTTP 200 with `{"status": "healthy", ...}`
2. Response includes `db_records` count and current `timestamp`
3. If database file is missing, returns HTTP 503 with `{"status": "unhealthy", "error": "..."}`
4. Existing endpoints (`/api/proposal-stats`, `/api/status.json`) unchanged
5. No new dependencies

## Scope
- **In scope**: Single endpoint in `zsiga/daemon.py`, read-only query
- **Out of scope**: UI, monitoring integration, alerting

## Risk
- **Impact**: Very low — read-only, no state mutation
- **Blast radius**: Single endpoint
- **Reversibility**: Delete the route and function
