# Budget Phase Reset and BUDGET_EXCEEDED Outcome

## ADDED Requirements

### Requirement: BUDGET_EXCEEDED Outcome Resolution Helper

A helper function `_resolve_budget_exceeded(result, default_outcome) -> Outcome` SHALL be added to `zsiga/pipeline/orchestrator.py`. It SHALL return `Outcome.FAIL` when `result.content == "BUDGET_EXCEEDED"`, otherwise return `default_outcome`. This centralizes the check so that every phase recording site uses the same logic.

This applies to all phase recording sites in the orchestrator: ENRICH, ENRICH retry (within Design Gate loop), IMPLEMENT, VERIFY, and any other phase that records a `PhaseRecord`.

#### Scenario: BUDGET_EXCEEDED content returns Outcome.FAIL

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::_resolve_budget_exceeded
- **Given** a `RunResult` with `content="BUDGET_EXCEEDED"` and `Outcome.SUCCESS` as the default
- **When** `_resolve_budget_exceeded(result, Outcome.SUCCESS)` is called
- **Then** it SHALL return `Outcome.FAIL`

#### Scenario: Normal content returns default Outcome.SUCCESS

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::_resolve_budget_exceeded
- **Given** a `RunResult` with `content="Here are the enriched specs..."` and `Outcome.SUCCESS` as the default
- **When** `_resolve_budget_exceeded(result, Outcome.SUCCESS)` is called
- **Then** it SHALL return `Outcome.SUCCESS`

#### Scenario: TIMEOUT content returns default Outcome.SUCCESS

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::_resolve_budget_exceeded
- **Given** a `RunResult` with `content="TIMEOUT"` and `Outcome.SUCCESS` as the default
- **When** `_resolve_budget_exceeded(result, Outcome.SUCCESS)` is called
- **Then** it SHALL return `Outcome.SUCCESS` — only the exact string `"BUDGET_EXCEEDED"` triggers the FAIL override

#### Scenario: STALE_LIMIT content returns default Outcome.SUCCESS

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::_resolve_budget_exceeded
- **Given** a `RunResult` with `content="STALE_LIMIT"` and `Outcome.SUCCESS` as the default
- **When** `_resolve_budget_exceeded(result, Outcome.SUCCESS)` is called
- **Then** it SHALL return `Outcome.SUCCESS`

#### Scenario: None content does not raise and returns default

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::_resolve_budget_exceeded
- **Given** a `RunResult` with `content=None` and `Outcome.SUCCESS` as the default
- **When** `_resolve_budget_exceeded(result, Outcome.SUCCESS)` is called
- **Then** it SHALL return `Outcome.SUCCESS` without raising an exception

## MODIFIED Requirements

### Requirement: Phase Budget Reset via AgentLoop.set_phase

The `AgentLoop.set_phase()` method SHALL reset the budget's internal counters (`_used`, `_extended`, `_consecutive_stale`) and value tracker. This ensures each phase starts with a fresh token accounting state. The orchestrator SHALL call `set_phase()` before each phase's `agent.run()` call.

The reset MUST occur before all four phase execution points:
1. ENRICH phase
2. ENRICH retry (triggered after Design Gate FAIL)
3. IMPLEMENT phase
4. VERIFY phase

#### Scenario: set_phase resets all budget counters

- **testable**: true
- **target**: zsiga/agent/loop.py::AgentLoop.set_phase
- **Given** an AgentLoop whose budget has `_used=500000`, `_extended=True`, `_consecutive_stale=3`
- **When** `set_phase("verify")` is called
- **Then** `budget._used` SHALL be `0`, `budget._extended` SHALL be `False`, and `budget._consecutive_stale` SHALL be `0`

#### Scenario: set_phase resets after partial ENRICH budget usage

- **testable**: false
- **Given** the ENRICH phase consumed 80% of its budget (`_used` close to limit)
- **When** the orchestrator calls `set_phase("implement")` before IMPLEMENT
- **Then** the IMPLEMENT phase SHALL start with `budget._used == 0` and the full configured limit available

#### Scenario: set_phase resets for ENRICH retry after BUDGET_EXCEEDED

- **testable**: false
- **Given** the ENRICH phase returned BUDGET_EXCEEDED (budget exhausted)
- **When** the orchestrator calls `set_phase("enrich")` before ENRICH retry
- **Then** the retry SHALL start with a fresh budget — the exhausted state from the failed ENRICH SHALL NOT carry over

### Requirement: BUDGET_EXCEEDED Warning Log

When a phase returns `BUDGET_EXCEEDED`, the orchestrator SHALL emit a WARNING-level log message containing the string `"BUDGET_EXCEEDED"` and the phase name (e.g. `"enrich"`, `"implement"`). This makes budget exhaustion observable in production logs without needing to inspect PhaseRecord outcomes.

#### Scenario: Warning logged on ENRICH BUDGET_EXCEEDED

- **testable**: false
- **Given** an orchestrator running the ENRICH phase
- **When** `agent.run()` returns `RunResult("BUDGET_EXCEEDED", ...)`
- **Then** a WARNING log containing `"BUDGET_EXCEEDED"` and `"enrich"` SHALL be emitted before the PhaseRecord is appended

#### Scenario: No warning when phase completes normally

- **testable**: false
- **Given** an orchestrator running the IMPLEMENT phase
- **When** `agent.run()` returns `RunResult("Implementation complete", ...)`
- **Then** no BUDGET_EXCEEDED-related warning SHALL be emitted
