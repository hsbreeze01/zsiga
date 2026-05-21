# Spec: Git Conflict Prevention During Branch Switching

## ADDED Requirements

### Requirement: Branch checkout SHALL succeed even when runtime files dirty the working tree

When the orchestrator needs to switch git branches (either to create a feature branch for IMPLEMENT or to return to deploy branch during cleanup), the system MUST ensure the working tree is clean before executing `git checkout`. This SHALL be achieved by committing all uncommitted changes — including untracked files — before any branch switch operation.

#### Scenario: Switch to feature branch with dirty working tree from CLARIFY phase
- **Given** the CLARIFY phase has written new files under `openspec/changes/<change_name>/` (e.g., `clarify.md`, `specs/`)
- **And** the working tree shows these as uncommitted changes
- **When** the orchestrator attempts to create/checkout the feature branch `zsiga/<change_name>`
- **Then** the system SHALL commit all uncommitted changes with a descriptive message BEFORE executing `git checkout`
- **And** the `git checkout` SHALL succeed without conflict

#### Scenario: Cleanup after proposal completion with runtime dirt
- **Given** the DELIVER phase has completed and runtime files (`data/zsiga.db`, `data/daemon_state.json`, etc.) have been modified during the pipeline
- **When** the orchestrator performs post-proposal cleanup to return to the deploy branch
- **Then** the system SHALL `reset_hard` to discard runtime dirt BEFORE executing `git checkout`
- **And** the `git checkout` to the deploy branch SHALL succeed without error

### Requirement: Post-checkout state SHALL be verified before proceeding

After any branch checkout, the system SHOULD verify that the current branch matches the expected branch name and that the working tree is clean. If verification fails, the system SHALL attempt one recovery `reset_hard` before reporting failure.

#### Scenario: Verify clean state after feature branch checkout
- **Given** the orchestrator has just checked out feature branch `zsiga/<change_name>`
- **When** the post-checkout verification runs
- **Then** the system SHALL confirm `current_branch()` equals `zsiga/<change_name>`
- **And** if uncommitted changes exist, the system SHALL commit them as a checkpoint before proceeding

### Requirement: Untracked daemon artifacts SHALL NOT block branch switching

Runtime artifacts such as `data/daemon.log`, `data/lock.pid`, and `data/daemon_state.json` are generated during pipeline execution. These files SHALL be handled gracefully during branch operations — they MUST NOT cause `git checkout` to abort.

#### Scenario: Daemon log file present during cleanup
- **Given** `data/daemon.log` exists as an untracked file on the feature branch
- **When** the cleanup logic runs to return to the deploy branch
- **Then** `reset_hard` (which includes `git clean -fd`) SHALL remove the untracked file
- **And** `git checkout` to deploy branch SHALL succeed
