# Delta Spec: Daemon Cycle Error Resilience

## MODIFIED Requirements

### REQ-DR-01: Per-Proposal Error Isolation in run_cycle

The daemon SHALL isolate errors on a per-proposal basis within `ZsigaOrchestrator.run_cycle()` so that a failure processing one proposal does not abort the entire cycle.

#### Scenario: Single proposal failure does not abort cycle

- **Given** `run_cycle()` has 3 active proposals
- **When** processing the second proposal raises an unhandled exception
- **Then** the exception SHALL be caught, logged with proposal ID and traceback
- **And** the cycle SHALL continue to process the third proposal
- **And** the cycle SHALL return the count of successfully processed proposals

#### Scenario: All proposals fail gracefully

- **Given** `run_cycle()` has 2 active proposals
- **When** both proposals raise unhandled exceptions
- **Then** each exception SHALL be caught and recorded as a lesson individually
- **And** the cycle SHALL return `processed=0`
- **And** the daemon SHALL continue to the next cycle without crashing

### REQ-DR-02: Orchestrator Construction Error Handling

The daemon loop SHALL catch and recover from errors during `ZsigaOrchestrator` construction, recording a structured lesson instead of crashing the daemon.

#### Scenario: AgentLoop creation fails

- **Given** the LLM API key is invalid or the API is unreachable
- **When** `ZsigaOrchestrator(config)` is called inside `daemon_loop`
- **Then** the exception SHALL be caught
- **And** a lesson SHALL be recorded with `pattern_key="daemon.cycle_error"`, exception type, and traceback
- **And** the daemon SHALL sleep for the idle poll interval and retry on the next cycle

#### Scenario: Memory context loading fails

- **Given** the memory context file is corrupted
- **When** `ZsigaOrchestrator._load_context()` raises an exception
- **Then** the orchestrator SHALL still be usable (context is optional)
- **And** a warning SHALL be logged

### REQ-DR-03: Structured Error Diagnostics in daemon_loop

The daemon loop SHALL record rich diagnostic information when a cycle error occurs, replacing the current `str(e)`-only lesson context.

#### Scenario: Cycle error records full traceback

- **Given** a cycle raises a `ConnectionError` during transport operation
- **When** the exception is caught in `daemon_loop`
- **Then** the recorded lesson SHALL include:
  - `context`: exception type name, first 500 chars of traceback, cycle number
  - `takeaway`: exception class name and a human-readable summary
- **And** the `pattern_key` SHALL be `"daemon.cycle_error"`

#### Scenario: Transient vs permanent error classification

- **Given** a cycle error occurs
- **When** the exception type is one of `(ConnectionError, TimeoutError, OSError)`
- **Then** the lesson `takeaway` SHALL include the tag `[transient]`
- **When** the exception type is anything else
- **Then** the lesson `takeaway` SHALL include the tag `[permanent]`
