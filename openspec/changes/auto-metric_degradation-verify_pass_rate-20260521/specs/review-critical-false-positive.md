# Spec: Review-Critical False Positive Prevention

## MODIFIED Requirements

### Requirement: Reviewer correctly detects implementation changes

The review phase SHALL correctly identify files that were created or modified during the implement phase. The reviewer MUST compare the git working tree state against the pre-implement baseline, not against an empty or stale file list. When implementation files exist and contain substantive changes, the reviewer SHALL NOT produce a "No implementation changes exist" rejection.

#### Scenario: New spec file created during implement is recognized

- **Given** the implement phase created a new file in `src/` with substantive content (≥ 10 lines of code)
- **And** the file is tracked in git as a new addition
- **When** the review phase evaluates the implementation
- **Then** the reviewer SHALL detect the new file via `git diff --name-status` or equivalent
- **And** the reviewer SHALL NOT emit "No implementation changes exist for any spec requirement"

#### Scenario: Modified existing file is recognized

- **Given** the implement phase modified an existing tracked file with substantive changes (≥ 3 lines changed)
- **And** the changes are staged or unstaged in the working tree
- **When** the review phase evaluates the implementation
- **Then** the reviewer SHALL detect the modification
- **And** SHALL NOT reject with a "no implementation changes" critical finding

#### Scenario: Only whitespace or trivial changes are correctly rejected

- **Given** the implement phase produced only whitespace changes or trivial modifications (< 3 substantive lines)
- **When** the review phase evaluates the implementation
- **Then** the reviewer MAY emit a "No implementation changes exist" finding
- **And** this SHALL be classified as a legitimate review rejection

### Requirement: Review rejection includes diff evidence

When the review phase produces a critical rejection (review-critical), the rejection message MUST include the actual diff summary that was used to make the determination, so that false positives can be diagnosed from logs alone.

#### Scenario: Critical rejection includes file list

- **Given** the reviewer rejects an implementation with a critical finding
- **When** the rejection is logged to `data/daemon.log` or `metrics/changes.jsonl`
- **Then** the log entry SHALL include the list of files detected as changed (even if empty)
- **And** SHALL include the diff command output or summary that led to the rejection
