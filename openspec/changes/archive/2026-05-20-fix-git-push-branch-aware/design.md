# Design: Fix Git Push — Branch-Aware + Error Handling

## Architecture Decision

**No structural changes** — only behavioral changes to existing functions in `git_ops.py` and the DELIVER block in `orchestrator.py`.

## Data Flow

### Current (broken)
```
push() → run_shell("git push origin main") → return (no exit_code check)
```
Result: failure is silent, DELIVER always reports SUCCESS.

### New (fixed)
```
push() → print("  git push origin <branch> ...")
       → run_shell("git push origin <branch>")
       → if exit_code != 0: print("  ❌ git push failed: ..."); raise RuntimeError
       → print("  ✅ pushed origin <branch>")
```
Result: failure propagates to orchestrator DELIVER handler → caught → FAIL outcome.

## Key Design Decisions

1. **RuntimeError for git failures** — Simple, unambiguous. Callers in orchestrator already have try/except blocks. No new exception hierarchy needed.
2. **Branch resolution in push/pull defaults** — `branch: str | None = None` with internal resolution via `current_branch()`. This is safe because `current_branch()` already exists and works. Callers that pass explicit branch (orchestrator DELIVER) are unaffected.
3. **No transport changes** — Both `LocalTransport` and `SSHTransport` already return `exit_code` in their dicts. The bug is that `git_ops` never checks it.
4. **Read-only functions unchanged** — `rev_parse`, `diff`, `has_uncommitted_changes`, `branch_exists`, `current_branch` already return data to callers and don't need exit_code enforcement. They stay as-is to minimize blast radius.

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/git_ops.py` | Add exit_code checking + logging to all mutating functions. Change `push()`/`pull()` default `branch` from `"main"` to `None` with dynamic resolution. |
| `zsiga/pipeline/orchestrator.py` | Wrap DELIVER git operations in try/except RuntimeError. On failure: log, set outcome=FAIL, record phase, return False. |
| `tests/test_git_ops.py` | **New file.** Unit tests for exit_code checking, branch resolution, logging, and error propagation. |

## DELIVER Phase Error Handling Flow

```
try:
    push(feature_branch)          # may raise
    checkout(deploy_branch)       # may raise
    pull(deploy_branch)           # may raise
    merge_branch(feature_branch)  # may raise
    push(deploy_branch)           # may raise
    delete_branch(feature_branch) # may raise (non-fatal, best-effort)
    print("  Merged ... and pushed")
except RuntimeError as e:
    print(f"  ❌ DELIVER failed: {e}")
    rec.outcome = Outcome.FAIL
    rec.phases.append(PhaseRecord(phase=Phase.DELIVER, outcome=Outcome.FAIL, detail=str(e)[:200]))
    return False
```

Note: `delete_branch` failure is non-fatal — the feature branch cleanup is best-effort and SHOULD be wrapped separately to avoid aborting an otherwise successful deliver.

## Backward Compatibility

- Callers that already pass explicit `branch` (orchestrator DELIVER) — unaffected.
- Callers that rely on `branch="main"` default — now get current branch instead, which is safer and always correct.
- `dry_run` mode in `push()` — unchanged, still returns early.
