# Design: Command Timeout Tracking

## Architecture Decision

The timeout tracking feature touches three layers of the existing metrics pipeline:

1. **Orchestrator** (`zsiga/pipeline/orchestrator.py`) — detect TIMEOUT from agent loop
2. **Collector** (`zsiga/metrics/collector.py`) — compute per-phase timeout rates
3. **Dashboard** (`zsiga/metrics/dashboard.py`) — render timeout stats and warnings

No new files are needed. No schema changes are needed — the `Outcome.TIMEOUT` enum
value already exists in `types.py`, and the `phases_json` blob in the DB already
stores `outcome` as a string. The data model already supports recording timeout;
what's missing is the detection and computation logic.

## Data Flow

```
AgentLoop.run()
  → returns RunResult(content="TIMEOUT") when elapsed > timeout_seconds
    ↓
Orchestrator._run_phases()
  → checks result content for "TIMEOUT"
  → creates PhaseRecord(outcome=Outcome.TIMEOUT)
  → records via collector.record_change()
    ↓
Collector.compute_stats()
  → iterates phase records, counts outcome=="timeout"
  → computes timeout_rate per phase
  → builds timeout_stats dict (total, worst, above threshold)
  → included in stats dict returned to dashboard
    ↓
Dashboard._render()
  → timeout summary card in stats grid
  → optional warning banner
  → timeout column in phase table
```

## Changes by File

### 1. `zsiga/pipeline/orchestrator.py`

In `_run_phases()`, after each call to `enrich()`, `implement()`, and `verify()`:

- Check if `result.content` equals `"TIMEOUT"` (or starts with `"TIMEOUT"`)
- If yes, set `outcome = Outcome.TIMEOUT` instead of `Outcome.SUCCESS`
- For ENRICH: still record the PhaseRecord, change continues (enrich timeout is
  non-fatal — the specs may have been partially written)
- For IMPLEMENT: record timeout, then still attempt mechanical verification
  (the agent may have written valid code before timing out)
- For VERIFY: record timeout, use `Outcome.TIMEOUT` in the PhaseRecord

Helper function `_is_timeout(result)` to check RunResult content.

### 2. `zsiga/metrics/collector.py`

In `compute_stats()`, inside the per-phase loop:

- Count `timeout_count = sum(1 for p in phase_records if p["outcome"] == "timeout")`
- Add `timeout_rate: round(timeout_count / len(phase_records) * 100, 1)` to phase stats

After the per-phase loop, compute `timeout_stats`:

```python
total_timeouts = sum(
    1 for c in changes for p in c.get("phases", [])
    if p["outcome"] == "timeout"
)
total_phase_records = sum(
    1 for c in changes for p in c.get("phases", [])
    if p["phase"] in ("enrich", "implement", "verify", "deliver")
)
timeout_rate_pct = round(total_timeouts / total_phase_records * 100, 1) if total_phase_records else 0

worst_phase = ""
worst_rate = 0
for phase_name, ps in phase_stats.items():
    tr = ps.get("timeout_rate", 0)
    if tr > worst_rate:
        worst_rate = tr
        worst_phase = phase_name

phases_above_threshold = [
    name for name, ps in phase_stats.items()
    if ps.get("timeout_rate", 0) > 20
]
```

Add `timeout_stats` to the returned stats dict.

Also add `timeout_rate: 0` to `_empty_stats()` phase_stats entries.

### 3. `zsiga/metrics/dashboard.py`

Three visual changes:

**a) Timeout summary card** — add to the stats grid in `_render()`:
```html
<div class="card">
  <div class="label">⏱️ Timeout Rate</div>
  <div class="value {_rate_class(timeout_rate)}">{timeout_rate}%</div>
  <div class="meta">{total_timeouts} timeouts across {num_phases} phases</div>
</div>
```

**b) Warning banner** — conditionally rendered before phase table when
`phases_above_threshold` is non-empty:
```html
<div class="section" style="...">
  ⚠️ High Timeout Warning: implement (30.0%), verify (25.0%)
  — consider increasing phase timeout configuration
</div>
```

**c) Phase table column** — add "Timeout Rate" column in `_phase_table()`:
Add `<th>Timeout Rate</th>` header and `<td class="{cls}">{timeout_rate}%</td>` cell.

## Frontend Notes

The dashboard is a server-generated HTML file (not a SPA). All rendering is done
in Python via f-string templates in `dashboard.py`. No JavaScript changes needed.
No frontend task requires manual work — all changes are Python template strings.
