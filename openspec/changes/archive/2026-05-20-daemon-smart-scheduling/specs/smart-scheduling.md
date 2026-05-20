# Spec: Smart Scheduling

## MODIFIED Requirements

### Requirement: Cycle Scheduling Policy

The daemon SHALL use an adaptive sleep policy instead of a fixed interval:

- When a cycle processes ≥ 1 change, the daemon SHALL immediately start the next cycle without sleeping.
- When a cycle processes 0 changes, the daemon SHALL sleep for `idle_poll_minutes` (default 5 minutes) before the next cycle.
- `cycle_interval_hours` SHALL be retained as a fallback but used ONLY when `idle_poll_minutes` is not configured.

#### Scenario: Pending changes processed continuously

```
Given a daemon with idle_poll_minutes=5 and 3 pending changes
When the daemon starts a cycle
Then it processes all 3 changes (up to max_changes_per_cycle per cycle)
And it immediately starts the next cycle without any sleep
```

#### Scenario: No pending changes — short poll

```
Given a daemon with idle_poll_minutes=5 and 0 pending changes
When the daemon completes a cycle that processes 0 changes
Then it sleeps for 5 minutes
Then it starts the next cycle
```

#### Scenario: New proposal arrives during idle poll

```
Given a daemon sleeping in idle_poll for 5 minutes
When a SIGUSR1 signal is NOT sent but the poll interval completes
Then the daemon starts the next cycle and picks up the new proposal
```

#### Scenario: Fallback to legacy interval

```
Given a daemon config with cycle_interval_hours=8 and no idle_poll_minutes configured
When the daemon completes a cycle with 0 changes
Then it sleeps for 8 hours (legacy behavior)
```

### Requirement: Safety Valve — Continuous Cycle Cooldown

The daemon SHALL prevent unbounded consecutive processing cycles:

- After `max_continuous_cycles` (default 20) consecutive cycles that each process ≥ 1 change, the daemon SHALL enter a forced cooldown of `cooldown_minutes` (default 30 minutes).
- The cooldown counter SHALL reset to 0 whenever a cycle processes 0 changes.
- The daemon SHALL log a warning when entering cooldown.

#### Scenario: Cooldown triggered after max continuous cycles

```
Given a daemon with max_continuous_cycles=3 and cooldown_minutes=10
When 3 consecutive cycles each process ≥ 1 change
Then the daemon sleeps for 10 minutes (cooldown)
And the continuous cycle counter resets to 0
```

#### Scenario: Cooldown counter resets on idle cycle

```
Given a daemon with max_continuous_cycles=3 and 2 consecutive busy cycles already completed
When the next cycle processes 0 changes
Then the continuous cycle counter resets to 0
And the daemon sleeps for idle_poll_minutes (not cooldown_minutes)
```

### Requirement: run_cycle Return Value

`ZsigaOrchestrator.run_cycle()` SHALL return an integer indicating the number of changes processed in that cycle.

#### Scenario: run_cycle returns processed count

```
Given a cycle that processes 2 changes successfully
When run_cycle completes
Then it returns the integer 2
```

#### Scenario: run_cycle returns zero on no work

```
Given a cycle with no pending proposals
When run_cycle completes
Then it returns the integer 0
```

## ADDED Requirements

### Requirement: Idle Poll Configuration

The pipeline configuration SHALL accept new scheduling parameters:

- `idle_poll_minutes` (int, default 5): sleep duration when no changes were processed
- `max_continuous_cycles` (int, default 20): consecutive busy cycles before forced cooldown
- `cooldown_minutes` (int, default 30): forced cooldown duration after max_continuous_cycles

These parameters SHALL be read from the `pipeline` section of `zsiga.yaml` with the specified defaults.

#### Scenario: Custom idle poll from config

```
Given zsiga.yaml with pipeline.idle_poll_minutes=3
When the daemon loads config
Then idle sleep duration is 3 minutes
```

#### Scenario: Default values when not configured

```
Given zsiga.yaml with no idle_poll_minutes key
When the daemon loads config
Then idle sleep duration defaults to 5 minutes
And max_continuous_cycles defaults to 20
And cooldown_minutes defaults to 30
```

### Requirement: Enhanced Daemon State

`daemon_state.json` SHALL include cumulative scheduling statistics:

- `total_cycles`: total number of cycles completed since daemon start
- `total_changes_processed`: total number of changes successfully processed since daemon start
- `idle_cycles`: current count of consecutive idle (zero-change) cycles
- `continuous_busy_cycles`: current count of consecutive busy (≥1 change) cycles
- `last_change_at`: ISO timestamp of the last cycle that processed ≥ 1 change

These fields SHALL be updated after every cycle.

#### Scenario: State updated after busy cycle

```
Given daemon_state.json with total_cycles=5 and total_changes_processed=3
When a cycle processes 2 changes
Then daemon_state.json shows total_cycles=6 and total_changes_processed=5
And last_change_at is updated to the current timestamp
And continuous_busy_cycles increments by 1
And idle_cycles resets to 0
```

#### Scenario: State updated after idle cycle

```
Given daemon_state.json with idle_cycles=0
When a cycle processes 0 changes
Then idle_cycles increments to 1
And continuous_busy_cycles resets to 0
And last_change_at is unchanged
```

#### Scenario: Existing signal handlers preserved

```
Given a running daemon with SIGUSR1/SIGUSR2/SIGTERM/SIGINT handlers
When the smart scheduling logic is active
Then SIGUSR1 still pauses the daemon after the current cycle
And SIGUSR2 still resumes the daemon
And SIGTERM/SIGINT still trigger graceful shutdown
```
