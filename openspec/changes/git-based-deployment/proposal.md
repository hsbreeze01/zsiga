# Proposal: Git-Based Deployment (铁律)

## Summary

所有代码变更必须通过 git branch → commit → push → pull 流程。禁止在生产目录直接修改代码。

## Implementation

### 1. zsiga.yaml: add deploy_branch per target
```yaml
targets:
  factory:
    deploy_branch: premium
  compass:
    deploy_branch: main
  # etc.
```

### 2. git_ops.py: add branch operations
- `create_feature_branch(target_path, change_name, transport)` — create zsiga/<name> from HEAD
- `checkout_branch(target_path, branch, transport)` — switch branch
- `merge_branch(target_path, source, transport)` — merge source into current

### 3. orchestrator.py: IMPLEMENT phase
- Before IMPLEMENT: checkout feature branch `zsiga/{change_name}`
- Agent edits on feature branch

### 4. orchestrator.py: DELIVER phase
- Push feature branch
- Checkout deploy_branch
- Pull latest
- Merge feature branch
- Push deploy_branch
- On REVERT: delete feature branch, checkout deploy_branch

## Expected Behavior
- All code changes go through git branch workflow
- Production only gets code via git pull
- Full traceability

## Constraints
- Scope: project=zsiga
- deploy_branch mapping: compass=main, all others=premium, zsiga=zsiga-l5-autonomous-engineer
