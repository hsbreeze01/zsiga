# Delta Spec: GitHub Issue Integration for Proposal-Commit Linkage

## ADDED Requirements

### REQ-GH-001: GitHub Issue SHALL be created for each successfully delivered proposal

When a proposal completes the DELIVER phase, the system SHALL create a GitHub Issue on the
target repository. The Issue title SHALL be derived from the proposal name, and the Issue body
SHALL contain the full proposal text. The Issue SHALL be labeled with `zsiga`.

#### Scenario: Successful proposal delivery creates a GitHub Issue
- **Given** a proposal has passed ENRICH, IMPLEMENT, VERIFY phases and is entering DELIVER
- **When** the DELIVER phase commits and pushes the change
- **Then** the system SHALL create a GitHub Issue via the GitHub REST API (`POST /repos/{owner}/{repo}/issues`)
- **And** the Issue title SHALL contain the change name
- **And** the Issue body SHALL contain the proposal markdown content
- **And** the Issue SHALL have the label `zsiga`

#### Scenario: GitHub Issue number is included in commit message
- **Given** a GitHub Issue was successfully created with number `N`
- **When** the system commits the delivered change
- **Then** the commit message SHALL contain `(closes #N)` so that GitHub auto-closes the Issue on push

#### Scenario: Revert commit references the Issue
- **Given** a change is reverted after a GitHub Issue `N` was created
- **When** the system creates the revert commit
- **Then** the revert commit message SHALL contain `(ref #N)`

### REQ-GH-002: GitHub Issue integration SHALL gracefully degrade on API failure

The DELIVER phase MUST NOT be blocked by GitHub API failures. If Issue creation fails for any
reason (timeout, rate limit, auth error, network error), the system SHALL log a warning and
proceed with the commit and push without an Issue reference.

#### Scenario: GitHub API is unreachable
- **Given** the GitHub API endpoint is unreachable or times out
- **When** the system attempts to create a GitHub Issue
- **Then** the system SHALL log a warning with the error details
- **And** the commit SHALL proceed without `(closes #N)` in the message
- **And** the DELIVER phase SHALL complete successfully

#### Scenario: GitHub API returns an authentication error
- **Given** `GITHUB_TOKEN` is missing, expired, or lacks repository permissions
- **When** the system attempts to create a GitHub Issue
- **Then** the system SHALL log a warning
- **And** the commit SHALL proceed without an Issue reference

#### Scenario: GitHub API returns a rate-limit error
- **Given** the GitHub API responds with HTTP 403 or 429
- **When** the system attempts to create a GitHub Issue
- **Then** the system SHALL log a warning and proceed without the Issue reference

### REQ-GH-003: GitHub integration SHALL be configurable and opt-in

The GitHub Issue integration SHALL be controlled by a `github` section in `zsiga.yaml`.
When `issue_integration` is `false` or the `github` section is absent, no GitHub API calls
SHALL be made.

#### Scenario: GitHub integration is enabled
- **Given** `zsiga.yaml` contains `github.issue_integration: true` and a valid `token` reference
- **When** a proposal reaches the DELIVER phase
- **Then** the system SHALL attempt to create a GitHub Issue

#### Scenario: GitHub integration is disabled
- **Given** `zsiga.yaml` does not contain a `github` section or `issue_integration` is `false`
- **When** a proposal reaches the DELIVER phase
- **Then** the system SHALL NOT attempt any GitHub API calls
- **And** the commit message SHALL use the existing format without Issue references

### REQ-GH-004: Repository owner/name SHALL be auto-detected from git remote

The system SHALL extract the `{owner}/{repo}` slug from the target repository's `git remote get-url origin`
output, supporting both SSH (`git@github.com:owner/repo.git`) and HTTPS (`https://github.com/owner/repo.git`) URL formats.
SSH config aliases (e.g., `github-agent`) SHALL be handled by parsing only the path component after the first colon.

#### Scenario: SSH URL with standard host
- **Given** the target's `git remote get-url origin` returns `git@github.com:hsbreeze01/myrepo.git`
- **When** the system extracts the repository slug
- **Then** the result SHALL be `hsbreeze01/myrepo`

#### Scenario: SSH URL with alias host
- **Given** the target's `git remote get-url origin` returns `git@github-agent:hsbreeze01/myrepo.git`
- **When** the system extracts the repository slug
- **Then** the result SHALL be `hsbreeze01/myrepo`

#### Scenario: HTTPS URL
- **Given** the target's `git remote get-url origin` returns `https://github.com/hsbreeze01/myrepo.git`
- **When** the system extracts the repository slug
- **Then** the result SHALL be `hsbreeze01/myrepo`

#### Scenario: Remote URL cannot be parsed
- **Given** the target's `git remote get-url origin` returns a non-GitHub URL or fails
- **When** the system attempts to extract the repository slug
- **Then** the result SHALL be `None`
- **And** the system SHALL skip Issue creation and proceed in degraded mode

## MODIFIED Requirements

### REQ-DELIVER-001: DELIVER phase commit message format

**Previously:** The commit message was `feat({project_name}): {change_name}`.

**Now:** The commit message SHALL be `feat({project_name}): {change_name} (closes #{issue_number})`
when a GitHub Issue was successfully created, or `feat({project_name}): {change_name}` when
Issue creation was skipped or failed.

#### Scenario: Commit message with Issue reference
- **Given** GitHub Issue `42` was created for change `add-feature-x`
- **When** the DELIVER phase commits on target `myrepo`
- **Then** the commit message SHALL be `feat(myrepo): add-feature-x (closes #42)`

#### Scenario: Commit message without Issue reference (degraded)
- **Given** GitHub Issue creation failed or is disabled
- **When** the DELIVER phase commits on target `myrepo`
- **Then** the commit message SHALL be `feat(myrepo): add-feature-x`
