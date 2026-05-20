# Design: Daemon Cycle Error Resilience

## Problem

The `daemon.cycle_error` pattern has occurred 6+ times. Root cause analysis reveals three structural weaknesses:

1. **No per-proposal isolation**: `run_cycle()` iterates proposals without try/except. Any unhandled exception in `decompose()`, `_process_change()`, or setup code aborts the entire cycle.

2. **Orchestrator construction outside error boundary**: `ZsigaOrchestrator(config)` is created before the try/except block in `daemon_loop`. If the constructor fails (LLM client creation, memory context loading), the daemon crashes entirely.

3. **Poor diagnostics**: The lesson records only `str(e)` as context — no traceback, no exception type, no classification of transient vs permanent errors. This makes root cause analysis impossible from the lessons alone.

## Architecture Decisions

### Decision 1: Per-proposal try/except in `run_cycle()` (REQ-DR-01)

Wrap each proposal iteration in a try/except block. On failure:
- Log the proposal ID, exception type, and traceback
- Record a lesson with `pattern_key="daemon.cycle_error"` and structured context
- Continue to the next proposal

This is the highest-impact fix — it prevents one bad proposal from wasting an entire cycle.

### Decision 2: Move orchestrator construction inside the try/except (REQ-DR-02)

Restructure the daemon_loop cycle body so `ZsigaOrchestrator(config)` is inside the try/except. On construction failure:
- Record a lesson with exception type and traceback
- The `finally` block skips `orchestrator.close()` if construction failed (use a flag)

### Decision 3: Rich error diagnostics (REQ-DR-03)

Use `traceback.format_exc()` to capture the full traceback. Include:
- Exception type name
- First 500 chars of traceback (to stay within lesson size limits)
- Cycle number
- Classification tag: `[transient]` for `ConnectionError/TimeoutError/OSError`, `[permanent]` for everything else

## Data Flow

```
daemon_loop cycle:
  1. Create ZsigaOrchestrator(config)  ← now inside try/except
  2. asyncio.run(orchestrator.run_cycle())
     └── run_cycle():
         ├── scanner.scan()            ← already safe (returns list)
         ├── for each proposal:
         │   └── try:
         │       ├── decompose()
         │       └── _process_change()
         │     except Exception:
         │       ├── log traceback
         │       ├── record_lesson(structured)
         │       └── continue  ← KEY CHANGE
         └── return processed count
  3. On any error:
     ├── classify as transient/permanent
     ├── record_lesson with full diagnostics
     └── continue to next cycle
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/pipeline/orchestrator.py` | Add per-proposal try/except in `run_cycle()` loop body |
| `zsiga/daemon.py` | Move orchestrator construction inside try/except; enrich error diagnostics with traceback + classification |

## Files to Add

| File | Purpose |
|------|---------|
| `tests/test_daemon_cycle_resilience.py` | Test per-proposal isolation, construction error recovery, structured diagnostics |

## Out of Scope

- Frontend changes: none needed
- Config changes: none needed
- New dependencies: `traceback` is stdlib
