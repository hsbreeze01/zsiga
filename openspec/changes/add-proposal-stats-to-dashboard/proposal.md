# add-proposal-stats-to-dashboard

## Summary
Add a `GET /api/proposal-stats` endpoint to the zsiga dashboard that returns aggregate proposal pipeline statistics from the SQLite database.

## Motivation
The dashboard currently shows daemon status and uptime but has no visibility into proposal pipeline health. Operators cannot see how many proposals have been accepted, rejected, or are in-flight without querying the database directly.

## Requirements
1. Add `GET /api/proposal-stats` endpoint to `zsiga/daemon.py`
2. Query the `changes` table to compute:
   - Total proposals count
   - Count by outcome (success, skipped, error, in_progress)
   - Average proposal duration (finished_at - started_at)
   - Recent 5 proposals with name, outcome, duration
3. Return JSON response matching existing API style
4. Must work with existing SQLite database at `data/zsiga.db`

## Success Criteria
- `curl http://localhost:8765/api/proposal-stats` returns valid JSON
- Response includes counts by outcome and recent proposals
- Existing endpoints (`/api/status`, `/`) continue to work
- No new dependencies required

## Risk Assessment
- **Impact**: Low — read-only query, no writes
- **Scope**: Single file change (daemon.py)
- **Reversibility**: Trivial — remove endpoint
