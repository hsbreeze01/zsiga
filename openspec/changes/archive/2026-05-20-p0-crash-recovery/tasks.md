# Tasks: P0 Crash Recovery

## 1. Phase WAL Module

- [ ] Create `zsiga/pipeline/phase_wal.py` with `PhaseWAL` class (write/read/delete/exists methods, JSON format, operates via transport)
- [ ] Create `tests/test_phase_wal.py` covering write-read round-trip, delete, read non-existent, and WAL at each phase boundary

## 2. Pre-flight Checkpoint + WAL Integration in Orchestrator

- [ ] Add pre-flight git checkpoint logic in `_run_phases()`: before IMPLEMENT, commit dirty tree as `"zsiga: checkpoint before {change_name}"` using existing `git_ops`
- [ ] Integrate PhaseWAL writes at each phase boundary (enrich/impl/verify) and WAL deletion on DELIVER success and on REVERT in `_run_phases()`

## 3. Crash Recovery Detection

- [ ] Add `_check_crash_recovery()` method on `ZsigaOrchestrator`: scan proposals for `.phase_state` + missing `verify.md`, rollback to `pre_sha`, delete WAL, archive, record lesson
- [ ] Add crash recovery tests in `tests/test_recovery.py` covering: crashed change detection + rollback, no-crash normal startup, already-complete change cleanup, recovery runs before cycle processing

## 4. Stale Lock PID Cleanup

- [ ] Modify `acquire_lock()` in `zsiga/daemon.py`: on flock failure, read PID, check liveness via `os.kill(pid, 0)`, clean stale lock and retry if dead
- [ ] Add stale lock tests in `tests/test_daemon_state.py` covering: dead PID cleanup, alive PID rejection, non-numeric lock content
