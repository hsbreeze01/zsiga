# Tasks: Git-Based Deployment

## Group 1: Config Layer

- [x] Add `deploy_branch` field to `TargetConfig` in `zsiga/config.py` (default `"main"`) and parse it from yaml in `load_config()`. Update `zsiga.yaml` to add `deploy_branch` per target: compass=main, factory/dataagent/stockshark/infopublisher=premium, zsiga=zsiga-l5-autonomous-engineer.

## Group 2: Git Operations Layer

- [x] Add 5 new functions to `zsiga/git_ops.py`: `branch_exists()`, `current_branch()`, `merge_branch()`, `delete_branch()`, `pull()`. All follow the existing pattern of accepting `(target_path, ..., transport)` with `LocalTransport` default.

## Group 3: Orchestrator IMPLEMENT Phase

- [x] Modify `_run_phases()` in `zsiga/pipeline/orchestrator.py`: before the pre-flight checkpoint, resolve the deploy_branch from config, ensure working tree is on feature branch `zsiga/{change_name}` (create if not exists, checkout if exists). Pass `deploy_branch` and `feature_branch` names through the rest of the phase.

## Group 4: Orchestrator DELIVER Phase

- [x] Modify the DELIVER section in `_run_phases()`: after commit+tag, push feature branch, checkout deploy_branch, pull, merge feature branch, push deploy_branch, delete feature branch. Ensure the working directory ends on deploy_branch.

## Group 5: Orchestrator REVERT Cleanup

- [ ] Modify all REVERT paths in `_run_phases()` (implement revert, verify revert): replace `reset_hard(pre_sha)` with checkout deploy_branch + delete feature branch. Also handle the `_fix_loop` and `_eval_fix_loop` escalation abort paths.

## Group 6: Tests

- [ ] Add `tests/test_git_branch_workflow.py` with unit tests: test `branch_exists`/`current_branch`/`merge_branch`/`delete_branch`/`pull` in git_ops (mocked transport), test TargetConfig deploy_branch default and override, test orchestrator branch naming logic.
