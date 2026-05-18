# Design: Session Timeline Renderer

## Overview

Add a pure-function `render_timeline(session: dict) -> str` to the `zsiga.metrics` package that takes a session summary dict (as exported by `export_session`) and returns a multi-line ASCII timeline visualizing each phase's duration as a proportional bar.

## Architecture Decision

**New module `zsiga/metrics/timeline.py`** — keeps timeline rendering separate from the HTML dashboard (`dashboard.py`), following the existing pattern where `collector.py` computes stats and `dashboard.py` renders HTML. The timeline module is a pure renderer with no DB or I/O dependencies.

## Data Flow

```
export_session() → session JSON dict
                          ↓
                render_timeline(session)
                          ↓
               multi-line ASCII string
                    ↓            ↓
              console log    <pre> in dashboard
```

## Input Schema

The function accepts a session dict with this shape (already produced by `export_session`):

```python
{
    "change_name": str,
    "outcome": str,          # "success" | "fail" | ...
    "started_at": str,       # ISO timestamp
    "finished_at": str,      # ISO timestamp
    "total_runtime_seconds": float,
    "phases": [
        {
            "phase": str,          # "enrich" | "implement" | "verify" | "deliver"
            "outcome": str,
            "seconds_used": float,
            "turns_used": int,
            "llm_calls": int,
            "tool_calls": int,
        },
        ...
    ]
}
```

## Output Format

```
═══ add-health-endpoint ═══ [SUCCESS]
──────────────────────────────────────────────
enrich     ███████████░░░░░░░░░░░░░░░░░░░░░░░░  45.0s  ✓
implement  ████████████████████████████████████░ 150.0s  ✓
verify     ████████████████░░░░░░░░░░░░░░░░░░░░  60.0s  ✓
deliver    ███████████░░░░░░░░░░░░░░░░░░░░░░░░░  45.0s  ✓
──────────────────────────────────────────────
Total: 300.0s │ 2026-05-15 14:00:00 → 14:05:00
```

Key formatting rules:
- Phase name left-padded to 12 chars for alignment
- Duration bar: max 40 chars using `█` (filled) + `░` (empty)
- Bar proportional to `phase.seconds_used / total_runtime_seconds`
- Outcome icon: ✓ success, ✗ fail, ⏱ timeout, ↩ reverted, – skipped/unknown
- Total runtime formatted human-readable (e.g., "5m 18s" or "45.0s")
- Timestamps displayed as `YYYY-MM-DD HH:MM:SS`

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `zsiga/metrics/timeline.py` | **CREATE** | `render_timeline()` function and helpers |
| `tests/test_timeline.py` | **CREATE** | Unit tests for all rendering scenarios |

No changes to existing files required — this is a purely additive feature.
