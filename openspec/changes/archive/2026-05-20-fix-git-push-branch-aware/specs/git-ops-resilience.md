# Delta Spec: Git Operations Resilience

## MODIFIED Requirements

### REQ-GO-01: All git write operations SHALL check exit_code and raise on failure

Every mutating git operation (`push`, `pull`, `commit`, `add_all`, `merge_branch`, `checkout`, `create_branch`, `delete_branch`, `tag`, `reset_hard`) in `git_ops.py` MUST inspect the `exit_code` returned by `transport.run_shell`. When `exit_code != 0`, the function SHALL print a diagnostic message including stderr and raise a `RuntimeError`.

#### Scenario: push to valid remote succeeds
- Given a target_path with a valid git remote
- When `git_ops.push(target_path, branch="feature/x", transport=transport)` is called
- Then the function SHALL print `  git push origin feature/x ...` before execution
- And SHALL print `  ✅ pushed origin feature/x` on success
- And SHALL return without raising

#### Scenario: push to invalid remote fails with error
- Given a target_path where the remote is unreachable
- When `git_ops.push(target_path, remote="bad-remote", branch="main", transport=transport)` is called
- Then the function SHALL print `  ❌ git push failed: <stderr content>`
- And SHALL raise `RuntimeError` with the stderr content

#### Scenario: pull with merge conflict fails with error
- Given a target_path where `git pull` produces a merge conflict
- When `git_ops.pull(target_path, transport=transport)` is called
- Then the function SHALL raise `RuntimeError`

#### Scenario: commit with no changes returns non-zero exit code
- Given a target_path with a clean working tree
- When `git_ops.commit(target_path, "msg", transport=transport)` is called
- Then the function SHALL raise `RuntimeError` (git returns exit code 1)

### REQ-GO-02: push() and pull() SHALL default to current branch, not hardcoded "main"

`git_ops.push()` and `git_ops.pull()` SHALL accept `branch: str | None = None`. When `branch` is `None`, the function MUST resolve the current branch via `current_branch()` and use that value. The default parameter value SHALL NOT contain any branch name string.

#### Scenario: push without explicit branch uses current branch
- Given a target_path on branch `zsiga/fix-123`
- When `git_ops.push(target_path, transport=transport)` is called with no `branch` argument
- Then the function SHALL resolve `branch = current_branch(target_path, transport)` → `"zsiga/fix-123"`
- And SHALL execute `git push origin zsiga/fix-123`

#### Scenario: push with explicit branch overrides current
- Given a target_path on branch `zsiga/fix-123`
- When `git_ops.push(target_path, branch="deploy", transport=transport)` is called
- Then the function SHALL execute `git push origin deploy` (explicit value takes precedence)

### REQ-GO-03: All git operations SHALL log before and after execution

Every function in `git_ops.py` SHALL print a "before" message showing the operation about to be performed, and an "after" message (✅) on success. On failure, the ❌ message is printed per REQ-GO-01.

#### Scenario: commit logs before and after
- Given a target_path with staged changes
- When `git_ops.commit(target_path, "feat: new feature", transport=transport)` is called
- Then the function SHALL print `  git commit -m 'feat: new feature' ...` before execution
- And SHALL print `  ✅ committed` on success

## ADDED Requirements

### REQ-GO-04: Remote name SHALL be configurable, never assumed "origin"

`git_ops.push()` and `git_ops.pull()` SHALL retain the `remote` parameter with a default of `"origin"`, but callers in `orchestrator.py` MUST pass the correct remote name from project config. The default is a safe fallback, not an assumption.

#### Scenario: push to custom remote
- Given a target_path configured with remote `github-agent`
- When `git_ops.push(target_path, remote="github-agent", branch="deploy", transport=transport)` is called
- Then the function SHALL execute `git push github-agent deploy`
