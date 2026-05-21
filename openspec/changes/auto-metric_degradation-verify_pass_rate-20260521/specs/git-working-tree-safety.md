# Spec: Git Working Tree Safety for Daemon Cycle

## ADDED Requirements

### Requirement: Robust pre-branch-switch cleanup

Before any `git checkout` that switches branches (feature branch creation or deployment branch return), the orchestrator SHALL ensure the working tree is clean by:

1. Running `git reset --hard` to the current HEAD to discard all uncommitted modifications
2. Running `git clean -fd` to remove untracked files

This SHALL happen regardless of whether `has_uncommitted_changes` reports dirty state, because runtime files (daemon state, metrics, DB) can be created between the check and the checkout.

#### Scenario: Dirty working tree from daemon runtime writes

- **Given** the daemon has written to `data/zsiga.db`, `data/daemon_state.json`, or `memory/learnings.jsonl` during the current cycle
- **And** these files appear as modified or untracked in `git status`
- **When** the orchestrator attempts to checkout a feature branch
- **Then** it SHALL first run `git reset --hard HEAD && git clean -fd`
- **And** the subsequent `git checkout` SHALL succeed without conflict errors

#### Scenario: Clean working tree (no-op)

- **Given** the working tree is already clean
- **When** the orchestrator performs the pre-branch-switch cleanup
- **Then** `git reset --hard HEAD` SHALL succeed as a no-op
- **And** no files SHALL be lost

### Requirement: Stash-based fallback for checkout conflicts

If `git checkout` fails with a conflict error (stderr contains `"would be overwritten by checkout"`), the orchestrator SHALL:

1. Run `git stash --include-untracked` to preserve all local changes
2. Retry the `git checkout`
3. After the checkout succeeds, run `git stash drop` to discard the stash (since the stashed files are runtime artifacts, not code changes)

This stash-based fallback SHALL NOT be used during the initial cleanup (where `reset --hard` is preferred), but only as a recovery when `reset --hard` itself fails or when the checkout still conflicts after reset.

#### Scenario: Checkout conflict despite reset

- **Given** `git reset --hard HEAD` completed but `git checkout <branch>` still fails with `"would be overwritten"` error
- **When** the stash-based fallback activates
- **Then** `git stash --include-untracked` SHALL succeed
- **And** the retry `git checkout <branch>` SHALL succeed
- **And** `git stash drop` SHALL be called to clean up

#### Scenario: Stash fallback not triggered for non-conflict errors

- **Given** `git checkout` fails with a non-conflict error (e.g., branch does not exist)
- **When** the orchestrator handles the error
- **Then** it SHALL NOT attempt the stash-based fallback
- **And** the original error SHALL propagate

### Requirement: Safe checkout utility function

The git operations module (`zsiga/git_ops.py`) SHALL expose a `safe_checkout` function that encapsulates the conflict-recovery logic:

- Parameters: `target_path`, `ref`, `transport`
- Behavior: attempt `git checkout`, on conflict error apply stash-based fallback
- Returns: nothing on success, raises `RuntimeError` on unrecoverable failure

#### Scenario: safe_checkout with clean tree

- **Given** the working tree is clean
- **When** `safe_checkout(target_path, "main")` is called
- **Then** it SHALL checkout `main` branch successfully

#### Scenario: safe_checkout with conflict recovery

- **Given** the working tree has uncommitted changes that conflict with the target ref
- **When** `safe_checkout(target_path, "main")` is called
- **Then** it SHALL stash changes, checkout `main`, and drop the stash

### Requirement: Post-proposal cleanup uses safe_checkout

The `_process_change` method's post-proposal cleanup block SHALL use `safe_checkout` instead of bare `git_ops.checkout` when switching back to the deploy branch.

#### Scenario: Post-proposal cleanup with dirty tree

- **Given** a proposal has completed (success or failure) and the working tree has runtime artifacts
- **When** the post-proposal cleanup runs
- **Then** it SHALL call `safe_checkout` to switch to the deploy branch
- **And** no `daemon.cycle_error` SHALL be recorded for this cleanup

### Requirement: Git safety has unit test coverage

The new `safe_checkout` function and the robust cleanup behavior SHALL have at minimum:
- One test for clean checkout (no stash needed)
- One test for checkout conflict that triggers stash fallback
- One test for unrecoverable checkout error (non-conflict)

#### Scenario: Test suite covers git safety

- **Given** the test suite is executed via `pytest`
- **When** the git safety tests run
- **Then** all 3 test cases SHALL pass

## MODIFIED Requirements

### Requirement: Pre-checkout cleanup uses reset-hard before safe_checkout

The existing pre-checkout cleanup in `_run_phases` (Phase 2: IMPLEMENT, before feature branch checkout) SHALL be modified to:

1. Run `git reset --hard HEAD` unconditionally (not just when `has_uncommitted_changes` is true)
2. Then call `safe_checkout` for the feature branch

#### Scenario: Pre-impl feature branch creation with reset

- **Given** the CLARIFY/ENRICH phases have written files to the working tree
- **When** the orchestrator prepares to create/checkout the feature branch
- **Then** it SHALL run `git reset --hard HEAD` first
- **And** then call `safe_checkout` for the feature branch
- **And** no `daemon.cycle_error` SHALL result from this operation
