# Spec: Phase Token Cap — TokenBudget

## ADDED Requirements

### Requirement: phase_cap attribute

`TokenBudget` SHALL accept a `phase_cap` parameter (default `0`) in its
constructor.  When `phase_cap > 0`, the budget tracks cumulative usage
against this per-phase ceiling independently from the session-level
`total_budget`.  When `phase_cap == 0` (the default), no per-phase limit
applies.

The `phase_cap` attribute SHALL be publicly readable and writable so the
orchestrator can set it before each phase.

#### Scenario: Default phase_cap is zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.__init__
- **Given** a newly constructed `TokenBudget()` with no `phase_cap` argument
- **When** the caller reads `budget.phase_cap`
- **Then** the value SHALL be `0`

#### Scenario: phase_cap set via constructor

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.__init__
- **Given** a `TokenBudget(phase_cap=200000)`
- **When** the caller reads `budget.phase_cap`
- **Then** the value SHALL be `200000`

#### Scenario: phase_cap is writable after construction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget
- **Given** a `TokenBudget()` with default `phase_cap=0`
- **When** the caller sets `budget.phase_cap = 400000`
- **Then** subsequent reads of `budget.phase_cap` SHALL return `400000`

### Requirement: cap_exceeded in record() result

`record()` SHALL include a `cap_exceeded` boolean in its return dict.
When `phase_cap > 0` and cumulative `_used` exceeds `phase_cap`,
`cap_exceeded` SHALL be `True`.  When `phase_cap == 0`, `cap_exceeded`
SHALL always be `False`.

The `cap_exceeded` check is computed as `_used > phase_cap` where `_used`
is the cumulative sum of all `prompt_tokens + completion_tokens` passed to
`record()` since the last counter reset.

#### Scenario: cap_exceeded is False when phase_cap is zero

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.record
- **Given** a `TokenBudget(total_budget=200000, phase_cap=0)`
- **When** `record(100000, 100000)` is called (total used=200000)
- **Then** the result dict SHALL contain `"cap_exceeded": False`

#### Scenario: cap_exceeded is False while within cap

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.record
- **Given** a `TokenBudget(phase_cap=200)`
- **When** `record(80, 70)` is called (used=150, under 200)
- **Then** the result dict SHALL contain `"cap_exceeded": False`

#### Scenario: cap_exceeded is True when usage exceeds cap

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.record
- **Given** a `TokenBudget(phase_cap=200)`
- **When** `record(120, 100)` is called (used=220 > 200)
- **Then** the result dict SHALL contain `"cap_exceeded": True`

#### Scenario: cap_exceeded triggers on subsequent call after accumulating

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.record
- **Given** a `TokenBudget(phase_cap=200)` with `record(80, 70)` already called (used=150)
- **When** `record(30, 30)` is called (used=210 > 200)
- **Then** the result dict SHALL contain `"cap_exceeded": True`

### Requirement: reset_phase() method

`TokenBudget` SHALL provide a `reset_phase()` method that resets `_used` to
zero WITHOUT resetting `_extended` or `_consecutive_stale`.  This differs
from `reset()` which resets all three counters.  The `phase_cap` attribute
SHALL NOT be changed by `reset_phase()`.

This method exists so callers can reset only the phase-scoped usage counter
without affecting session-level soft-extension or stale-tracking state.

#### Scenario: reset_phase resets only _used counter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.reset_phase
- **Given** a `TokenBudget(total_budget=600000, phase_cap=100)` with
  `record(60, 50)` already called (used=110, cap_exceeded=True)
- **When** `reset_phase()` is called
- **Then** a subsequent `record(10, 10)` SHALL return `"cap_exceeded": False`
  (used=20, under cap 100)

#### Scenario: reset_phase preserves _extended state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.reset_phase
- **Given** a `TokenBudget(total_budget=100)` where `try_extend("productive")`
  has been called (so `_extended=True` and `effective_budget=150`)
- **When** `reset_phase()` is called
- **Then** `_extended` SHALL remain `True` and `effective_budget` SHALL remain `150`

#### Scenario: reset_phase preserves _consecutive_stale

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.reset_phase
- **Given** a `TokenBudget()` where `record(10, 10, value_signal="stale")` has
  been called 3 times (so `_consecutive_stale=3`)
- **When** `reset_phase()` is called
- **Then** `_consecutive_stale` SHALL remain `3`

#### Scenario: reset_phase does not change phase_cap

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.reset_phase
- **Given** a `TokenBudget(phase_cap=200000)`
- **When** `reset_phase()` is called
- **Then** `phase_cap` SHALL remain `200000`

### Requirement: Backward compatibility

When `phase_cap == 0` (the default), `TokenBudget` SHALL behave identically
to its pre-change behavior.  The `record()` return dict gains a new
`"cap_exceeded": False` key but no other behavioral changes.  Existing
`total_budget` enforcement, `per_turn_limit`, `session_exceeded`,
`effective_budget`, and `try_extend()` semantics SHALL remain unchanged.

#### Scenario: Existing session_exceeded enforcement unaffected by phase_cap

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.record
- **Given** a `TokenBudget(total_budget=1000, phase_cap=0)`
- **When** `record(600, 500)` is called (used=1100 > 1000)
- **Then** `session_exceeded` SHALL be `True` and `cap_exceeded` SHALL be `False`

#### Scenario: Both caps can be exceeded simultaneously

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.record
- **Given** a `TokenBudget(total_budget=1000, phase_cap=500)`
- **When** `record(600, 500)` is called (used=1100, exceeding both caps)
- **Then** both `session_exceeded` and `cap_exceeded` SHALL be `True`

#### Scenario: snapshot() still works with phase_cap

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/agent/token_budget.py::TokenBudget.snapshot
- **Given** a `TokenBudget(total_budget=100000, phase_cap=50000)` with some usage recorded
- **When** `snapshot()` is called
- **Then** it SHALL return a valid dict with all existing keys present

