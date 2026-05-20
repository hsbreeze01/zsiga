# Design: Daemon Smart Scheduling

## Architecture Decision

Replace the fixed `cycle_interval_hours * 3600` sleep with a state-machine–style scheduler inside `daemon_loop()`. The scheduler tracks consecutive busy/idle cycles and decides the next action based on `run_cycle()` return value.

**Why state-machine approach:** The scheduling logic is purely local to `daemon_loop()` — no new classes needed. A few local variables (`continuous_busy`, `idle_count`) plus the existing `DaemonState` are sufficient. Adding a separate scheduler class would over-abstract a 20-line conditional.

## Data Flow

```
daemon_loop()
  │
  ├─ run_cycle() → int (processed_count)
  │
  ├─ if processed_count > 0:
  │     continuous_busy += 1
  │     idle_count = 0
  │     if continuous_busy >= max_continuous_cycles:
  │         sleep(cooldown_minutes * 60)   ← safety valve
  │         continuous_busy = 0
  │     else:
  │         continue                        ← immediate next cycle
  │
  └─ if processed_count == 0:
        idle_count += 1
        continuous_busy = 0
        sleep(idle_poll_minutes * 60)       ← short poll
```

## File Changes

### 1. `zsiga/config.py` — Add scheduling parameters to PipelineConfig

- Add constructor params: `idle_poll_minutes=5`, `max_continuous_cycles=20`, `cooldown_minutes=30`
- Add attribute assignments in `__init__`
- Parse from `pipeline_raw` in `load_config()` with defaults

### 2. `zsiga/daemon.py` — Smart scheduling in daemon_loop + enhanced state

- Modify `_write_daemon_state()` signature: add optional params `total_cycles`, `total_changes_processed`, `idle_cycles`, `continuous_busy_cycles`, `last_change_at`
- Add these new fields to the JSON output
- Modify `daemon_loop()`:
  - Track `continuous_busy` and total counters locally
  - Call `run_cycle()` and capture return value
  - Branch on processed count for sleep decision
  - Call `_write_daemon_state()` with updated stats after each cycle
  - Replace `interval = config.pipeline.cycle_interval_hours * 3600` with adaptive logic
- Keep all signal handler registrations unchanged
- Keep PID lock, dashboard thread, and finally block unchanged

### 3. `zsiga/pipeline/orchestrator.py` — Return processed count

- Change `run_cycle()` to `return processed` at end of method
- `processed` is already tracked as a local variable in the method

### 4. `tests/test_daemon_state.py` — Add tests for new scheduling behavior

- Test `_write_daemon_state` with new fields
- Test smart scheduling logic (mocked `run_cycle` returning different counts)
- Test safety valve triggers at max_continuous_cycles
- Test idle poll interval used when processed_count == 0
- Test fallback to cycle_interval_hours when idle_poll_minutes not configured

## Configuration Schema (zsiga.yaml)

```yaml
pipeline:
  cycle_interval_hours: 8      # kept as fallback
  idle_poll_minutes: 5         # NEW — default 5
  max_continuous_cycles: 20    # NEW — default 20
  cooldown_minutes: 30         # NEW — default 30
```

## Compatibility

- **Backward compatible:** If `idle_poll_minutes` is absent, fallback to `cycle_interval_hours * 3600` for idle sleep (original behavior)
- **Signal handling unchanged:** SIGUSR1/2/TERM/INT handlers remain identical
- **daemon_state.json additive:** New fields are added; existing fields unchanged. Consumers that ignore unknown keys are unaffected.
