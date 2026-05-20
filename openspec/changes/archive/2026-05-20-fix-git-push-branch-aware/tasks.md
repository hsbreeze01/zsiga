# Tasks: Fix Git Push — Branch-Aware + Error Handling

## 1. git_ops.py — Exit Code Checking + Logging + Branch Defaults

- [x] **1.1** Add `_check_result()` helper and apply to all mutating functions in `git_ops.py`
  - Add a private `_check_result(result, operation_label)` helper that checks `exit_code != 0`, prints `❌` + stderr, raises `RuntimeError`
  - Apply to: `add_all`, `commit`, `tag`, `push`, `create_branch`, `checkout`, `merge_branch`, `delete_branch`, `reset_hard`
  - Add before/after logging (`print(f"  git <op> ...")` / `print(f"  ✅ <past-tense>")`) to each function
  - Change `push()` default: `branch: str = "main"` → `branch: str | None = None`, resolve via `current_branch()` when None
  - Change `pull()` default: `branch: str = "main"` → `branch: str | None = None`, resolve via `current_branch()` when None
  - Keep `dry_run` early-return in `push()` unchanged

- [x] **1.2** Add unit tests for `git_ops.py` error handling
  - New file `tests/test_git_ops.py`
  - Test: push failure (mock transport returning exit_code=1) raises RuntimeError with stderr message
  - Test: push success prints before/after and returns cleanly
  - Test: push with no branch arg resolves current branch via mock
  - Test: pull with no branch arg resolves current branch via mock
  - Test: commit failure (exit_code=1) raises RuntimeError
  - Test: merge failure raises RuntimeError
  - Test: checkout failure raises RuntimeError
  - Test: delete_branch failure raises RuntimeError
  - Test: tag failure raises RuntimeError

## 2. Orchestrator DELIVER — Error Handling

- [x] **2.1** Wrap DELIVER git operations in try/except with FAIL outcome
  - In `_run_phases()` DELIVER section, wrap `push → checkout → pull → merge → push` sequence in `try/except RuntimeError`
  - On exception: print `❌ DELIVER failed: {e}`, set `rec.outcome = Outcome.FAIL`, append `PhaseRecord(Phase.DELIVER, Outcome.FAIL, detail=str(e)[:200])`, `return False`
  - Wrap `delete_branch` separately as best-effort (log warning on failure, don't abort)
  - Verify all explicit `branch=` params are already correct (feature_branch / deploy_branch) — they are

- [x] **2.2** Add integration test for DELIVER failure handling
  - In `tests/test_git_ops.py` or existing test file
  - Test: mock `git_ops.push` to raise RuntimeError during DELIVER → outcome is FAIL, not SUCCESS
  - Test: mock `git_ops.merge_branch` to raise → outcome is FAIL

## 3. Verification

- [x] **3.1** Run full test suite and lint
  - `python -m pytest tests/ -x`
  - `ruff check zsiga/git_ops.py zsiga/pipeline/orchestrator.py`
  - Ensure all existing tests still pass
