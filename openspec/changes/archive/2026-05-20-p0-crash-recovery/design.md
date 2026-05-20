# Design: P0 Crash Recovery

## Architecture Decisions

### AD-1: Phase WAL as a standalone module

**Decision:** Create `pipeline/phase_wal.py` as an independent module with a `PhaseWAL` class.

**Rationale:** The WAL has a single responsibility (write/read/delete a JSON file via transport).
Keeping it separate from the orchestrator makes it testable in isolation and reusable by the
daemon's crash recovery scanner. The class wraps transport calls, so it works identically for
local and SSH targets.

### AD-2: Checkpoint before IMPLEMENT via existing git_ops

**Decision:** Reuse `git_ops.has_uncommitted_changes()`, `git_ops.add_all()`, and `git_ops.commit()`
to create the pre-flight checkpoint. No new git operations needed.

**Rationale:** The orchestrator already captures `pre_sha` before IMPLEMENT. We add a conditional
commit if the tree is dirty, which gives us a clean rollback point without introducing new
abstractions.

### AD-3: Crash recovery in orchestrator.run_cycle()

**Decision:** Add `_check_crash_recovery()` as a method on `ZsigaOrchestrator`, called at the top
of `run_cycle()` before the main loop processes proposals.

**Rationale:** The orchestrator already has access to all transports and the config. Scanning
for `.phase_state` files in active changes uses the same `DirectoryScanner` logic. Keeping
recovery in the orchestrator avoids coupling the daemon to pipeline internals.

### AD-4: Stale lock cleanup in acquire_lock()

**Decision:** Modify `acquire_lock()` in `daemon.py` to check PID liveness via `os.kill(pid, 0)`
before failing. If the PID is dead, remove the lock file and retry acquisition.

**Rationale:** This is the simplest possible fix — a single function change with no new modules.
`os.kill(pid, 0)` is the standard POSIX way to check process liveness without sending a signal.

## Data Flow

### Normal Phase Execution (with WAL)

```
_run_phases()
  ├── Phase ENRICH → write WAL (phase="enrich")
  ├── Pre-flight checkpoint (commit dirty tree if needed)
  ├── Phase IMPLEMENT → write WAL (phase="implement", pre_sha=...)
  ├── Phase VERIFY → write WAL (phase="verify")
  ├── Phase DELIVER → delete WAL
  └── On any REVERT → delete WAL
```

### Crash Recovery Flow

```
run_cycle()
  ├── _check_crash_recovery()
  │     ├── Scan all proposals from scanner
  │     ├── For each proposal: check .phase_state exists AND verify.md missing
  │     ├── If crashed:
  │     │     ├── git reset --hard to pre_sha
  │     │     ├── delete .phase_state
  │     │     ├── archive change
  │     │     └── record lesson
  │     └── Continue to normal processing
  └── Normal proposal loop (existing code)
```

### Lock Acquisition Flow (with stale cleanup)

```
acquire_lock()
  ├── Try fcntl.flock(LOCK_EX | LOCK_NB)
  ├── On failure:
  │     ├── Read PID from lock file
  │     ├── Try os.kill(pid, 0)
  │     ├── If OSError (process dead):
  │     │     ├── Remove stale lock file
  │     │     ├── Print warning
  │     │     └── Retry flock acquisition
  │     └── If process alive: fail with existing error
  └── On success: write current PID
```

## Files to Create / Modify

| File | Action | Description |
|------|--------|-------------|
| `zsiga/pipeline/phase_wal.py` | **CREATE** | PhaseWAL class with write/read/delete/exists |
| `zsiga/pipeline/orchestrator.py` | MODIFY | Add WAL writes at phase boundaries, pre-flight checkpoint, crash recovery scan |
| `zsiga/daemon.py` | MODIFY | Stale lock PID cleanup in `acquire_lock()` |
| `tests/test_phase_wal.py` | **CREATE** | Unit tests for PhaseWAL module |
| `tests/test_recovery.py` | MODIFY | Add crash recovery detection tests |
