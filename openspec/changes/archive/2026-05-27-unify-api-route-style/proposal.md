# unify-api-route-style

## Summary
Standardize all HTTP API routes in `zsiga/daemon.py` to use consistent `/api/<resource>` style (no `.json` suffix), while keeping old routes as redirects for backward compatibility.

## Problem
Current routes are inconsistent:
- `/api/status.json` — has `.json` suffix
- `/api/metrics.json` — has `.json` suffix
- `/api/current.json` — has `.json` suffix
- `/api/health` — no suffix
- `/api/proposal-stats` — no suffix

The `.json` suffix is redundant (all responses are JSON) and inconsistent with newer endpoints.

## Technical Design
Modify single file: `zsiga/daemon.py`

1. Rename routes:
   - `/api/status.json` → `/api/status`
   - `/api/metrics.json` → `/api/metrics`
   - `/api/current.json` → `/api/current`
2. Add backward-compatible redirects: old `.json` routes return 301 to new routes
3. Keep `/api/health` and `/api/proposal-stats` unchanged

## Acceptance Criteria
1. `curl http://localhost:58175/api/status` returns 200 with same JSON as old `/api/status.json`
2. `curl http://localhost:58175/api/status.json` returns 301 redirect to `/api/status`
3. Same for `/api/metrics` and `/api/current`
4. `/api/health` and `/api/proposal-stats` unchanged
5. No new dependencies

## Scope
- **In scope**: Route renaming + redirects in `zsiga/daemon.py`
- **Out of scope**: Dashboard UI changes, new endpoints

## Risk
- **Impact**: Low — HTTP 301 preserves backward compatibility
- **Reversibility**: Revert route names
