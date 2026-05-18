# Tasks: Implement Retry with Backoff Utility

## Group 1: Core Implementation

- [x] 1.1 Add `retry_with_backoff` async function and `retry_sync` sync function to `zsiga/pipeline/utils.py`
  - Includes: delay computation with exponential backoff, jitter via `random.uniform`, `max_delay` cap, `retry_on` exception filtering, stdout logging of retry attempts
  - Parameters: `fn`, `max_attempts=3`, `base_delay=1.0`, `max_delay=30.0`, `jitter=True`, `retry_on=(Exception,)`
  - Estimated: 2 rounds (write + lint)

## Group 2: Tests

- [x] 2.1 Create `tests/test_retry_backoff.py` with full scenario coverage
  - Includes: first-attempt success, retry-then-success, exhaust-all-attempts, exception filtering (non-retryable raises immediately), backoff timing without jitter, jitter range validation, max_delay cap, sync retry, logging output verification
  - Estimated: 2 rounds (write + verify)
