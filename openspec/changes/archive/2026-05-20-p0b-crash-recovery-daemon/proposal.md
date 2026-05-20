# Proposal: P0b Crash Recovery — Daemon Detection + Stale Lock

## Summary

Complete the crash recovery system: add `_check_crash_recovery()` to daemon.py for startup crash detection, and stale lock.pid cleanup in `acquire_lock()`.

## Context

P0 was partially implemented: `phase_wal.py` exists, orchestrator has pre-flight checkpoint and WAL writes. But two critical pieces are missing:

1. **Daemon crash recovery detection** — daemon.py has no `_check_crash_recovery()` function
2. **Stale lock.pid cleanup** — `acquire_lock()` has no stale PID detection

## Implementation

### 1. Crash Recovery Detection (`daemon.py`)

Add function `_check_crash_recovery(config)`:
- Scan non-archived changes in openspec/changes/
- For each: check if has `.phase_state` file AND no `verify.md`
- If found: read .phase_state → get pre_sha, target_path, project
- Create transport for that project
- `git_ops.reset_hard(target_path, pre_sha, transport)`
- Delete .phase_state
- Archive the change
- Log warning with change name and phase

Call at top of `daemon_loop()` after `acquire_lock()`, before first cycle.

### 2. Stale Lock Cleanup (`daemon.py`)

In `acquire_lock()`, when flock fails:
- Read existing PID from lock file
- `os.kill(pid, 0)` to check if process is alive
- If `ProcessLookupError`: stale lock → unlink and re-acquire
- If alive: report and exit as before

## Expected Behavior
- Daemon restart after crash → auto-detect incomplete change → rollback
- Stale lock.pid from crashed process → auto-cleanup

## Constraints
- Scope: project=zsiga, files: daemon.py only
- Do NOT modify orchestrator.py or phase_wal.py (already done)
