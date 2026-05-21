# Spec: Daemon Checkout Conflict Recovery

## ADDED Requirements

### Requirement: Auto-stash before git checkout

When the daemon cycle performs a `git checkout` operation and the working tree contains uncommitted changes to tracked files, the daemon SHALL automatically stash those changes before proceeding with checkout, rather than failing with a checkout conflict error.

#### Scenario: Uncommitted data files during branch switch

- **Given** the daemon is running a cycle on a change directory
- **And** files such as `data/zsiga.db`, `data/daemon_state.json`, `memory/learnings.jsonl`, or `metrics/changes.jsonl` have been modified but not committed
- **When** the daemon attempts `git checkout` to switch context
- **Then** the daemon SHALL automatically execute `git stash` (with a descriptive message) before the checkout
- **And** the checkout SHALL succeed without raising `RuntimeError`

#### Scenario: Uncommitted openspec change files during branch switch

- **Given** the daemon is processing a change with generated spec files, clarify.md, or phase_state
- **And** those files are modified but not committed in the working tree
- **When** the daemon attempts `git checkout`
- **Then** the daemon SHALL stash uncommitted changes before checkout
- **And** the cycle SHALL continue without aborting

### Requirement: Stash restore after checkout

After a successful checkout that was preceded by an auto-stash, the daemon SHALL attempt to restore the stashed changes if they are relevant to the target branch, ensuring operational continuity.

#### Scenario: Restoring stashed state on target branch

- **Given** the daemon auto-stashed changes before checkout
- **And** the checkout to the target branch succeeded
- **When** the daemon continues the cycle
- **Then** the daemon SHALL attempt `git stash pop` to restore the stashed changes
- **And** if stash pop produces a conflict, the daemon SHALL log a warning and continue (not abort)

### Requirement: Checkout conflict no longer counts as verify failure

The verify pipeline SHALL NOT record a "checkout conflict" as a verify-stage failure. Checkout conflicts are operational issues, not code quality failures.

#### Scenario: Metrics classification of checkout conflict

- **Given** a daemon cycle encounters a checkout conflict
- **And** the auto-stash mechanism resolves it
- **When** the cycle outcome is recorded to `metrics/changes.jsonl`
- **Then** the event SHALL be classified as an operational recovery, not a verify failure
- **And** the `verify_pass_rate` metric SHALL NOT be penalized for auto-recovered checkout conflicts
