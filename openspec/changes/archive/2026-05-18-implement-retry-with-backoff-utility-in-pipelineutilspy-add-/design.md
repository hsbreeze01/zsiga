# Design: Retry with Backoff Utility

## Architecture Decision

Add retry-with-backoff primitives directly into `zsiga/pipeline/utils.py`, which is the existing utility module for pipeline helpers. This avoids introducing a new module for a small, self-contained feature and keeps the import graph flat.

## Why Not a Decorator?

The proposal mentions "decorator" but the primary consumers are:
1. `AgentLoop.run()` — calls `self.client.chat.completions.create()` (LLM API)
2. `Transport.run_shell()` — subprocess calls that may fail transiently (SSH timeout, etc.)

Both call sites invoke specific methods, not top-level async functions. A **function wrapper** (`retry_with_backoff` / `retry_sync`) is more flexible than a decorator for wrapping method calls or lambda expressions. A decorator is an optional future enhancement.

## Data Flow

```
Caller (e.g., AgentLoop or pipeline phase)
  │
  ├─ retry_with_backoff(fn, ..., retry_on, max_attempts, base_delay, max_delay, jitter)
  │     │
  │     ├─ attempt 1: await fn()
  │     │   ├─ success → return result
  │     │   └─ exception in retry_on → compute delay → asyncio.sleep(delay) → next attempt
  │     ├─ attempt 2: ...
  │     └─ attempt N: raise last exception
  │
  └─ retry_sync(fn, ...)  — same logic with time.sleep instead of asyncio.sleep
```

## Delay Computation

```
raw_delay = base_delay * (2 ** attempt_index)   # attempt_index is 0-based
raw_delay = min(raw_delay, max_delay)

if jitter:
    delay = random.uniform(raw_delay * 0.5, raw_delay)
else:
    delay = raw_delay
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/pipeline/utils.py` | Add `retry_with_backoff` (async) and `retry_sync` (sync) functions |
| `tests/test_retry_backoff.py` | New test file with full coverage of all scenarios |

## Integration Points (Future, not in this change)

- `zsiga/agent/loop.py` — wrap `self.client.chat.completions.create()` call with retry for transient LLM API errors
- `zsiga/transport.py` — wrap `subprocess.run()` in `SSHTransport.run_shell()` with retry for SSH timeouts

These integrations are intentionally out of scope for this change. This change delivers the utility; subsequent changes will wire it into consumers.
