# Tasks: Daemon Smart Scheduling

## Group 1: Configuration Layer

- [x] **1.1** Add `idle_poll_minutes`, `max_continuous_cycles`, `cooldown_minutes` parameters to `PipelineConfig.__init__()` with defaults (5, 20, 30) and parse them from `pipeline_raw` in `load_config()`
  - Files: `zsiga/config.py`
  - Scope: Add 3 constructor params + 3 `pipeline_raw.get()` calls + 3 attribute assignments

## Group 2: Orchestrator Return Value

- [x] **2.1** Make `ZsigaOrchestrator.run_cycle()` return `processed` (int) — the variable already exists and is tracked; add `return processed` at end of method
  - Files: `zsiga/pipeline/orchestrator.py`
  - Scope: Single `return processed` statement addition at end of `run_cycle()`

## Group 3: Daemon State Enhancement

- [x] **3.1** Extend `_write_daemon_state()` to accept and write new fields: `total_cycles`, `total_changes_processed`, `idle_cycles`, `continuous_busy_cycles`, `last_change_at`
  - Files: `zsiga/daemon.py`
  - Scope: Extend function signature with optional params, add to JSON dict

## Group 4: Smart Scheduling Logic

- [x] **4.1** Rewrite `daemon_loop()` cycle-end scheduling to use adaptive sleep: capture `run_cycle()` return value, branch on `processed_count > 0` (immediate continue) vs `== 0` (sleep `idle_poll_minutes`), with safety valve at `max_continuous_cycles` forcing `cooldown_minutes` sleep; track `continuous_busy`, total counters; pass updated stats to `_write_daemon_state()`
  - Files: `zsiga/daemon.py`
  - Scope: Replace the fixed-interval sleep block (lines ~198-224) with adaptive scheduling logic; keep signal handling, PID lock, dashboard thread, finally block unchanged

## Group 5: Tests

- [x] **5.1** Add tests for enhanced `_write_daemon_state()` with new fields (`total_cycles`, `total_changes_processed`, `idle_cycles`, `continuous_busy_cycles`, `last_change_at`), and test that omitting new params omits those keys (backward compat)
  - Files: `tests/test_daemon_state.py`

- [ ] **5.2** Add tests for smart scheduling in `daemon_loop()`: mock `run_cycle()` to return various counts, verify immediate continue when busy, short sleep when idle, cooldown triggered at max_continuous_cycles, fallback to `cycle_interval_hours` when `idle_poll_minutes` not set
  - Files: `tests/test_daemon_state.py` (or new `tests/test_daemon_scheduling.py`)
