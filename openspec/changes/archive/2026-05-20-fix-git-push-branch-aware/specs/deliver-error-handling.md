# Delta Spec: DELIVER Phase Error Handling

## MODIFIED Requirements

### REQ-DL-01: DELIVER phase SHALL treat git operation failures as fatal

In `_run_phases()` (DELIVER section), if any `git_ops` call raises `RuntimeError`, the orchestrator SHALL catch the error, log it, set `rec.outcome = Outcome.FAIL`, record the phase as `Outcome.FAIL`, and return `False`. The pipeline SHALL NOT silently continue after a push or merge failure.

#### Scenario: push of feature branch fails — DELIVER outcome is FAIL
- Given a successful IMPLEMENT and VERIFY phase
- And the DELIVER phase starts
- When `git_ops.push()` for the feature branch raises `RuntimeError("push failed: ...")`
- Then the orchestrator SHALL print the error
- And SHALL set `rec.outcome = Outcome.FAIL`
- And SHALL append a `PhaseRecord(phase=Phase.DELIVER, outcome=Outcome.FAIL, detail=...)` 
- And SHALL return `False`
- And SHALL NOT attempt checkout/merge/push of deploy branch

#### Scenario: merge fails — DELIVER outcome is FAIL
- Given feature branch push succeeded
- And checkout to deploy branch succeeded
- When `git_ops.merge_branch()` raises `RuntimeError`
- Then the orchestrator SHALL print the error
- And SHALL set `rec.outcome = Outcome.FAIL`
- And SHALL return `False`

#### Scenario: all DELIVER steps succeed — normal flow unchanged
- Given all git operations succeed
- Then the DELIVER phase SHALL record `Outcome.SUCCESS` and return `True` as before

### REQ-DL-02: DELIVER SHALL use branch-aware push/pull — no hardcoded branch names

The DELIVER section in `_run_phases()` SHALL call `git_ops.push()` and `git_ops.pull()` with explicit `branch` parameter set to `feature_branch` and `deploy_branch` respectively. It SHALL NOT rely on default parameter values that contain hardcoded branch names.

#### Scenario: DELIVER pushes feature branch explicitly
- Given feature_branch = "zsiga/fix-123" and deploy_branch = "main"
- When the DELIVER phase runs
- Then `git_ops.push(target_path, branch=feature_branch, transport=transport)` SHALL be called
- And `git_ops.pull(target_path, branch=deploy_branch, transport=transport)` SHALL be called
- And `git_ops.push(target_path, branch=deploy_branch, transport=transport)` SHALL be called
