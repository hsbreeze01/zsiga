# Spec: Verify Failure Classification

## ADDED Requirements

### Requirement: Verify failure records SHALL be classifiable by root cause category

The system MUST classify each verify-phase failure into one of the following root cause categories:
- `git_conflict` — daemon cycle error caused by dirty working tree during branch checkout
- `lint_violation` — ruff check errors on changed files (E701, E702, E401, E741, etc.)
- `test_failure` — pytest failures on changed test targets
- `no_implementation` — zero diff between pre-impl SHA and HEAD (empty implementation)
- `verdict_unknown` — verifier LLM output did not contain parseable Verdict line
- `review_critical` — review phase found CRITICAL issues that blocked progression
- `other` — any failure not matching the above categories

#### Scenario: Classify a git conflict failure
- **Given** a ChangeRecord with verify phase outcome "fail" and detail containing "Your local changes to the following files would be overwritten by checkout"
- **When** the failure classifier processes this record
- **Then** the classifier SHALL return category `git_conflict`

#### Scenario: Classify a lint violation failure
- **Given** a ChangeRecord with implement phase outcome "fail" and detail starting with "lint:" containing ruff error codes
- **When** the failure classifier processes this record
- **Then** the classifier SHALL return category `lint_violation`

#### Scenario: Classify a verdict parse failure
- **Given** a ChangeRecord with verify phase outcome "fail" and no detail text
- **When** the failure classifier processes this record
- **Then** the classifier SHALL return category `verdict_unknown`

### Requirement: Verify failure classification SHALL produce a summary report with counts and percentages

The classifier MUST output a report containing:
- Total verify-phase failures analyzed
- For each category: count, percentage of total, and list of affected change names
- Top-2 categories by count flagged as "high-frequency root causes"

#### Scenario: Generate classification report from recent failures
- **Given** 50 ChangeRecords of which 25 have verify phase outcome "fail"
- **And** 15 of those failures match `git_conflict` category
- **And** 7 match `lint_violation` category
- **When** the classifier generates a summary report
- **Then** the report SHALL show `git_conflict` count=15 (60.0%) and `lint_violation` count=7 (28.0%)
- **And** the report SHALL flag `git_conflict` and `lint_violation` as high-frequency root causes
