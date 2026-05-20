# Proposal: P0 Crash Recovery — Pre-flight Checkpoint + Phase WAL + Lock Cleanup

## Summary

Add crash recovery guarantees: pre-flight git checkpoints before IMPLEMENT, phase state WAL for resume detection, and stale lock.pid auto-cleanup on daemon restart.

## Motivation

If zsiga crashes during IMPLEMENT (OOM, segfault, timeout), the target project's code is left in an unknown state. The daemon can't restart because lock.pid is stale. Zero recovery mechanism today.

## Implementation

### 1. Phase WAL Module (`pipeline/phase_wal.py` — NEW FILE)
- PhaseWAL class with write/read/delete/exists methods
- Operates on `<change_dir>/.phase_state` via transport
- JSON format: {"current_phase", "started_at", "pre_sha", "target_path", "project"}

### 2. Pre-flight Checkpoint (`orchestrator.py`)
- Before IMPLEMENT: force-commit dirty state as "zsiga: checkpoint before {change_name}"
- Write WAL at each phase boundary (enrich/impl/verify/deliver)
- Delete WAL on DELIVER success and on REVERT

### 3. Crash Recovery Detection (`daemon.py`)
- `_check_crash_recovery(config)`: scan for incomplete changes (has design.md + .phase_state, no verify.md)
- Rollback target to pre_sha via transport
- Delete .phase_state, archive change, log warnings
- Call at top of daemon_loop() after acquire_lock()

### 4. Stale Lock PID Cleanup (`daemon.py`)
- In acquire_lock(): check if existing PID is alive via os.kill(pid, 0)
- If dead: clean stale lock and re-acquire
- Log warning

## Expected Behavior
- Every IMPLEMENT starts from a clean git checkpoint
- Crash → daemon restart → auto-detect → rollback → archive
- Stale lock.pid no longer blocks restart

## Constraints
- Scope: project=zsiga
- All changes must pass pytest and ruff
