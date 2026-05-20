# Design: Git-Based Deployment

## Architecture Decision

Introduce a feature-branch workflow where all agent code modifications happen on isolated `zsiga/<change_name>` branches. The deploy branch (configured per target) only receives code via merge during DELIVER. This ensures production stability and full traceability.

**Why feature branches instead of direct commit to deploy branch?**
- Prevents half-finished code from being `git pull`-ed into production
- Enables clean revert: just delete the feature branch
- Maintains full git history of what the agent attempted

## Data Flow

```
IMPLEMENT phase:
  1. checkout deploy_branch → pull latest
  2. create_feature_branch("zsiga/{change_name}") from HEAD
  3. (agent edits files on feature branch)
  4. checkpoint commit on feature branch

DELIVER phase (on success):
  1. commit any remaining changes on feature branch
  2. push feature branch to remote
  3. checkout deploy_branch
  4. pull deploy_branch from remote
  5. merge feature branch into deploy_branch
  6. push deploy_branch to remote
  7. tag on deploy_branch
  8. delete feature branch (local)

REVERT (on failure):
  1. checkout deploy_branch
  2. delete feature branch
```

## Changes Required

### 1. `zsiga/config.py` — TargetConfig + load_config
- Add `deploy_branch: str` field to `TargetConfig` (default `"main"`)
- Parse `deploy_branch` from yaml in `load_config()`

### 2. `zsiga/git_ops.py` — New git operations
- Add `branch_exists(target_path, branch_name, transport)` — check if branch exists
- Add `current_branch(target_path, transport)` — get current branch name
- Add `merge_branch(target_path, source, transport)` — merge source into current
- Add `delete_branch(target_path, branch_name, transport)` — delete a branch
- Add `pull(target_path, remote, branch, transport)` — pull from remote

### 3. `zsiga/pipeline/orchestrator.py` — Phase modifications

**IMPLEMENT phase (`_run_phases`):**
- Before pre-flight checkpoint: ensure on feature branch `zsiga/{change_name}`
  - If branch exists → checkout it
  - If not → create from current HEAD (deploy branch)
- Pre-flight checkpoint commit stays on feature branch

**DELIVER phase (inside `_run_phases`):**
- After commit + tag:
  - push feature branch
  - checkout deploy_branch
  - pull deploy_branch
  - merge feature branch
  - push deploy_branch
  - delete feature branch

**REVERT paths (inside `_run_phases`):**
- Instead of `reset_hard(pre_sha)`: checkout deploy_branch, delete feature branch
- Applies to: implement revert, verify revert, eval-fix revert

### 4. `zsiga.yaml` — Add deploy_branch per target
- compass: `deploy_branch: main`
- All others: `deploy_branch: premium`
- zsiga (self): `deploy_branch: zsiga-l5-autonomous-engineer`

## Files Modified
- `zsiga/config.py` — TargetConfig + load_config
- `zsiga/git_ops.py` — 5 new functions
- `zsiga/pipeline/orchestrator.py` — IMPLEMENT/DELIVER/REVERT flow
- `zsiga.yaml` — deploy_branch per target
- `tests/test_git_branch_workflow.py` — new test file (unit tests for git_ops + config)
- `tests/test_config.py` — extend existing config test if present

## Files NOT Modified
- `zsiga/transport.py` — no changes needed, git operations use existing transport
- `zsiga/pipeline/implementer.py` — no changes, agent edits files normally on feature branch
- `site/dashboard.html` — no frontend changes needed
