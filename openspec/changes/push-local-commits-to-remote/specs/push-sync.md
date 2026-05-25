# push-sync

## ADDED Requirements

### Requirement: Pre-flight state validation

Before any push operation, the local repository state SHALL be validated to ensure a clean and correct starting point.

#### Scenario: Working directory is clean before push

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_preflight_working_directory_clean
- **Given** the repository at `/home/zsiga/repo`
- **When** `git status --porcelain` is executed
- **Then** the output SHALL contain no entries for tracked files under `zsiga/`, `tests/`, `site/`, or any Python source file — only spec/test artifacts from the current change directory may appear as untracked

#### Scenario: Current branch is zsiga-l5-autonomous-engineer

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_preflight_correct_branch
- **Given** the repository at `/home/zsiga/repo`
- **When** `git branch --show-current` is executed
- **Then** the output SHALL be `zsiga-l5-autonomous-engineer`

#### Scenario: Local is ahead of remote with expected commit count

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_preflight_local_ahead_of_remote
- **Given** the repository at `/home/zsiga/repo` with `origin` remote fetched
- **When** `git rev-list --count origin/zsiga-l5-autonomous-engineer..HEAD` is executed
- **Then** the count SHALL be greater than zero, confirming local has commits not yet on the remote

### Requirement: Local-to-remote branch synchronization

The local branch `zsiga-l5-autonomous-engineer` SHALL be pushed to `origin/zsiga-l5-autonomous-engineer` so that the remote ref advances to match the local HEAD. If the direct push is rejected due to remote divergence, a rebase strategy SHALL be applied before retry.

#### Scenario: Push succeeds without conflict

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_remote_head_matches_local_head
- **Given** the local branch `zsiga-l5-autonomous-engineer` has commits not present on `origin/zsiga-l5-autonomous-engineer`, and no new commits exist on the remote
- **When** `git push origin zsiga-l5-autonomous-engineer` is executed
- **Then** `git log -1 --format=%H origin/zsiga-l5-autonomous-engineer` SHALL output the same commit hash as `git log -1 --format=%H HEAD`, and `git status` SHALL report the branch is up to date with `origin/zsiga-l5-autonomous-engineer`

#### Scenario: Push rejected due to remote divergence triggers rebase

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_push_rejected_triggers_rebase
- **Given** the remote `origin/zsiga-l5-autonomous-engineer` has commits not in the local branch
- **When** the initial `git push` is rejected
- **Then** the system SHALL execute `git pull --rebase origin zsiga-l5-autonomous-engineer` to resolve divergence, followed by a retry of `git push origin zsiga-l5-autonomous-engineer`

### Requirement: Post-push verification

After the push operation completes, the repository state SHALL be verified to confirm successful synchronization with zero side effects.

#### Scenario: No commit divergence after sync

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_no_divergence_after_sync
- **Given** the push (with optional rebase) has completed
- **When** `git log --oneline origin/zsiga-l5-autonomous-engineer...HEAD` is executed
- **Then** the output SHALL be empty, indicating zero commits of divergence between local and remote

#### Scenario: No source code files are modified

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_no_source_files_modified
- **Given** the push operation has completed
- **When** `git diff --name-only HEAD` is checked
- **Then** the output SHALL be empty — no tracked source files SHALL be modified by this operation

#### Scenario: Remote branch not behind local after sync

- **testable**: true
- **target**: tests/test_spec_push_local_commits_to_remote__push_sync.py::test_branch_not_behind_after_sync
- **Given** the push operation has completed
- **When** `git status --porcelain --branch` is executed
- **Then** the output SHALL NOT contain the word "behind"
