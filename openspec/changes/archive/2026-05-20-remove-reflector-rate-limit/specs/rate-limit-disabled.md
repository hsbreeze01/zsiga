# Spec: Reflector Rate Limit Disabled

## MODIFIED Requirements

### REQ-1: Rate limit gate always allows proposals

The `_rate_limit_reached` method on `Reflector` SHALL return `False` unconditionally,
effectively disabling the 3-per-24h rate limit on auto-generated proposals.

The method MUST be retained (not deleted) so that it can be re-enabled in a future
growth phase.

#### Scenario: Reflector is not blocked by recent proposal count

- **Given** a base directory with 5 proposals recorded in `reflector_history.jsonl` within the last 24 hours
- **When** `should_propose(signal, base)` is called with a non-duplicate signal and no external proposals
- **Then** the method SHALL return `True` (proposal generation is allowed)

#### Scenario: Rate limit method is preserved for future use

- **Given** the `Reflector` class
- **When** `_rate_limit_reached(base)` is called with any base path
- **Then** it SHALL return `False`
- **And** the method signature SHALL remain `def _rate_limit_reached(self, base: Path) -> bool`

### REQ-2: Rate-limit tests updated to reflect disabled behavior

The `TestShouldProposeRateLimit` test class in `tests/test_reflector.py` SHALL be updated
so that all tests assert the new behavior (rate limit never blocks proposals).

#### Scenario: Former rate-limit-at-3 test now allows proposals

- **Given** a base directory with 3 entries in `reflector_history.jsonl` within the last 24 hours
- **When** `should_propose(signal, base)` is called with a non-duplicate signal
- **Then** the result SHALL be `True`

#### Scenario: Under-rate-limit test continues to pass unchanged

- **Given** a base directory with 1 entry in `reflector_history.jsonl` within the last 24 hours
- **When** `should_propose(signal, base)` is called with a non-duplicate signal
- **Then** the result SHALL be `True`
