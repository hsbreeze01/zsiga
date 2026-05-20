# Tasks: Daemon Cycle Error Resilience

## Group 1: Per-Proposal Error Isolation

- [x] **1.1** Add per-proposal try/except in `ZsigaOrchestrator.run_cycle()` (in `zsiga/pipeline/orchestrator.py`)
  - Wrap the proposal iteration body (decompose + _process_change) in try/except
  - On exception: log proposal ID + exception, record a lesson with `pattern_key="daemon.cycle_error"`, continue to next proposal
  - Import `traceback` for structured error info
  - Estimated: 1 round (read confirmed, write + verify)

## Group 2: Daemon Loop Error Boundary Enhancement

- [x] **2.1** Move `ZsigaOrchestrator(config)` inside the try/except in `daemon_loop()` (in `zsiga/daemon.py`)
  - Restructure so orchestrator construction is protected
  - Handle the case where construction fails (skip `orchestrator.close()` in finally)
  - Estimated: 1 round

- [x] **2.2** Enrich error diagnostics in daemon_loop exception handler (in `zsiga/daemon.py`)
  - Import `traceback` at top of file
  - Replace bare `str(e)` context with: exception type, traceback excerpt (500 chars), cycle number
  - Add transient/permanent classification: `[transient]` for ConnectionError/TimeoutError/OSError, `[permanent]` for others
  - Update the `takeaway` field to include the classification tag and exception class name
  - Estimated: 1 round

## Group 3: Tests

- [x] **3.1** Add test file `tests/test_daemon_cycle_resilience.py` with tests for:
  - Per-proposal isolation: mock `run_cycle` with proposals where the 2nd one throws; verify 1st and 3rd still process
  - Orchestrator construction failure: mock `ZsigaOrchestrator.__init__` to raise; verify lesson is recorded and daemon continues
  - Structured diagnostics: verify lesson context includes exception type, traceback excerpt, and `[transient]`/`[permanent]` tag
  - Estimated: 1 round
