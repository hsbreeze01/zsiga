# Tasks: Remove Reflector Rate Limit

## 1. Core change

- [x] **1.1** Disable rate limit in `_rate_limit_reached` and update rate-limit tests
  - File: `zsiga/intake/reflector.py` — change method body to `return False`
  - File: `tests/test_reflector.py` — update `TestShouldProposeRateLimit` test assertions
  - Verify: `pytest tests/test_reflector.py` passes, `ruff check` clean
