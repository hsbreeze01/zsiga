# Git Branch Workflow

## ADDED Requirements

### Requirement: Feature Branch Isolation

All code modifications produced by the IMPLEMENT phase SHALL be committed on a dedicated feature branch named `zsiga/<change_name>`, isolated from the deploy branch.

#### Scenario: Feature branch created before IMPLEMENT starts
- Given a change "fix-login-bug" targeting project "factory" with deploy_branch "premium"
- When the IMPLEMENT phase begins
- Then the orchestrator SHALL create a feature branch `zsiga/fix-login-bug` branching from the current HEAD of the deploy branch
- And the working directory SHALL be switched to the feature branch before any code modifications

#### Scenario: Feature branch already exists (crash recovery)
- Given a feature branch `zsiga/fix-login-bug` already exists from a previous interrupted run
- When the IMPLEMENT phase begins
- Then the orchestrator SHALL checkout the existing feature branch instead of creating a new one
- And SHALL NOT fail due to the branch already existing

---

### Requirement: Deliver via Merge to Deploy Branch

After successful VERIFY, the DELIVER phase SHALL merge the feature branch into the configured deploy branch and push, ensuring production only receives code via git merge.

#### Scenario: Successful delivery merges feature into deploy branch
- Given a change "fix-login-bug" on feature branch `zsiga/fix-login-bug` that passed IMPLEMENT and VERIFY
- And the deploy_branch for the target is "premium"
- When the DELIVER phase executes
- Then the orchestrator SHALL commit any uncommitted changes on the feature branch
- And checkout the deploy branch "premium"
- And pull the latest from remote for "premium"
- And merge `zsiga/fix-login-bug` into "premium"
- And push "premium" to remote
- And delete the feature branch `zsiga/fix-login-bug`
- And the working directory SHALL end on the deploy branch "premium"

#### Scenario: Deploy branch defaults when not configured
- Given a target with no deploy_branch configured in zsiga.yaml
- When the DELIVER phase executes
- Then the deploy_branch SHALL default to "main"

---

### Requirement: Revert Cleans Up Feature Branch

When a change is REVERTED (implementation failed or verification failed), the orchestrator SHALL restore the deploy branch state and delete the feature branch.

#### Scenario: Revert during IMPLEMENT phase
- Given a change "fix-login-bug" on feature branch `zsiga/fix-login-bug` that failed mechanical verification
- When the orchestrator triggers a revert
- Then the orchestrator SHALL checkout the deploy branch
- And delete the feature branch `zsiga/fix-login-bug`
- And the working directory SHALL end on the deploy branch in a clean state

#### Scenario: Revert during VERIFY phase
- Given a change "fix-login-bug" on feature branch `zsiga/fix-login-bug` that failed VERIFIER evaluation
- When the orchestrator triggers a revert
- Then the orchestrator SHALL checkout the deploy branch
- And delete the feature branch `zsiga/fix-login-bug`
- And the working directory SHALL end on the deploy branch in a clean state

---

### Requirement: Deploy Branch Configuration

Each target in zsiga.yaml SHALL accept an optional `deploy_branch` field that specifies which branch receives merged code during DELIVER.

#### Scenario: Target with explicit deploy_branch
- Given a target "factory" with `deploy_branch: premium` in zsiga.yaml
- When the config is loaded
- Then the TargetConfig for "factory" SHALL have `deploy_branch = "premium"`

#### Scenario: Target without deploy_branch
- Given a target "compass" without `deploy_branch` in zsiga.yaml
- When the config is loaded
- Then the TargetConfig for "compass" SHALL have `deploy_branch = "main"` (default)

---

### Requirement: No Direct Modification of Deploy Branch During IMPLEMENT

The deploy branch MUST NOT receive any commits during the IMPLEMENT, fix, or VERIFY phases. All changes MUST only exist on the feature branch.

#### Scenario: Pre-flight checkpoint commits to feature branch
- Given the IMPLEMENT phase detects uncommitted changes before starting
- When the pre-flight checkpoint runs
- Then the checkpoint commit SHALL be made on the feature branch
- And the deploy branch SHALL remain unchanged
