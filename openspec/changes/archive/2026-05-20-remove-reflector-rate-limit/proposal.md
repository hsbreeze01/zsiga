# Proposal: Remove Reflector Rate Limit

## Summary

Change `_rate_limit_reached()` in `intake/reflector.py` to always return False.

## Implementation

Single method change:
```python
def _rate_limit_reached(self, base: Path) -> bool:
    """Rate limit disabled during early growth phase."""
    return False
```

Keep method (not delete) so it can be re-enabled later.

## Constraints
- Scope: project=zsiga, file=intake/reflector.py, single method
