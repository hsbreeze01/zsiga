# Delta Spec: Retry with Backoff Utility

## ADDED Requirements

### Requirement: Async Retry with Exponential Backoff

The system SHALL provide an async retry utility function `retry_with_backoff` in `zsiga/pipeline/utils.py` that wraps any async callable with configurable retry behavior.

#### Scenario: Successful call on first attempt

- **Given** an async function that returns a value without raising
- **When** `retry_with_backoff` is called with `max_attempts=3`
- **Then** the function SHALL be invoked exactly once and return the result immediately

#### Scenario: Retry on transient exception then succeed

- **Given** an async function that raises a transient exception on the first 2 calls and succeeds on the 3rd
- **When** `retry_with_backoff` is called with `max_attempts=3` and the exception type is in `retry_on`
- **Then** the function SHALL be retried up to 3 times and return the successful result

#### Scenario: Exhaust all attempts and raise last exception

- **Given** an async function that always raises a transient exception
- **When** `retry_with_backoff` is called with `max_attempts=3`
- **Then** the function SHALL raise the last caught exception after 3 attempts

### Requirement: Exponential Backoff with Jitter

The system SHALL compute delay between retries using exponential backoff with optional jitter to avoid thundering-herd effects.

#### Scenario: Default backoff timing

- **Given** `base_delay=1.0`, `max_delay=30.0`, and `jitter=False`
- **When** the 1st, 2nd, and 3rd retries occur
- **Then** the delays SHALL be 1.0s, 2.0s, 4.0s respectively (doubled each time, capped at `max_delay`)

#### Scenario: Jitter randomizes delay

- **Given** `base_delay=1.0`, `max_delay=30.0`, and `jitter=True`
- **When** a retry occurs
- **Then** the actual delay SHALL be between `base_delay * 0.5` and `base_delay * 2^attempt`, never exceeding `max_delay`

#### Scenario: Delay capped at max_delay

- **Given** `base_delay=1.0`, `max_delay=10.0`, and `jitter=False`
- **When** the 5th retry occurs (delay would be 16.0s without cap)
- **Then** the actual delay SHALL be exactly `max_delay` (10.0s)

### Requirement: Configurable Exception Filtering

The system SHALL allow callers to specify which exception types trigger a retry.

#### Scenario: Only specified exceptions are retried

- **Given** `retry_on=(ConnectionError, TimeoutError)` and the function raises `ValueError`
- **When** `retry_with_backoff` is called
- **Then** the `ValueError` SHALL be raised immediately without retry

#### Scenario: Default retries on all exceptions

- **Given** `retry_on` is not specified (defaults to `(Exception,)`)
- **When** any exception is raised
- **Then** the function SHALL be retried up to `max_attempts`

### Requirement: Retry Logging

The system SHALL log retry events to stdout for observability.

#### Scenario: Retry attempt logged

- **Given** an async function that fails twice then succeeds
- **When** `retry_with_backoff` retries
- **Then** each retry SHALL print a message including attempt number, exception type, and delay in seconds

### Requirement: Synchronous Helper for Transport Operations

The system SHALL provide a synchronous counterpart `retry_sync` that applies the same backoff logic to non-async callables, for use with transport `run_shell` calls.

#### Scenario: Sync retry on failed transport command

- **Given** a sync function that raises `subprocess.TimeoutExpired` on the first call
- **When** `retry_sync` is called with `retry_on=(subprocess.TimeoutExpired,)` and `max_attempts=2`
- **Then** the function SHALL be retried once and return the successful result
