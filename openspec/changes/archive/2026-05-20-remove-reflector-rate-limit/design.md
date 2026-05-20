# Design: Remove Reflector Rate Limit

## Decision

Disable the reflector's per-24h proposal rate limit (`_rate_limit_reached`) by making it
unconditionally return `False`. The method is kept intact so it can be re-enabled later
when the project matures past the early growth phase.

The dedup gate (`_is_duplicate`) and external-proposal gate (`_has_external_proposals`)
remain unchanged — they still prevent wasteful duplicate proposals.

## Rationale

- During the early growth phase, the project benefits from more frequent self-reflection
  proposals. A 3-per-24h cap is overly conservative.
- Keeping the method (vs deleting it) means re-enabling is a one-line change later.

## Files Changed

| File | Action |
|---|---|
| `zsiga/intake/reflector.py` | Modify `_rate_limit_reached` body to `return False` |
| `tests/test_reflector.py` | Update `TestShouldProposeRateLimit` assertions to match new behavior |

## Data Flow (unchanged)

```
scan_signals() → [Signal] → should_propose(signal)
                                  ├─ _has_external_proposals()  (still active)
                                  ├─ _rate_limit_reached()      (now always False)
                                  └─ _is_duplicate()            (still active)
                              → True/False
```
