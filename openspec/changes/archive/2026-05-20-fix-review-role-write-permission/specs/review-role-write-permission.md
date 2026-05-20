# Delta Spec: Review Role Write Permission

## MODIFIED Requirements

### REQ-1: Review sub-agent SHALL possess file-writing capability

The `Role.REVIEW` configuration SHALL include `write_file` in its `allowed_tools` list, enabling the review sub-agent to persist its review output to `{change_dir}/review.md`.

#### Scenario: Review sub-agent writes review.md successfully

- **Given** a change directory exists at `{change_dir}`
- **And** the review phase is initiated via `run_review()`
- **When** the review sub-agent executes and produces a verdict
- **Then** the sub-agent SHALL have access to the `write_file` tool
- **And** SHALL write its review output to `{change_dir}/review.md`

#### Scenario: Review sub-agent does NOT receive edit_file

- **Given** the `Role.REVIEW` configuration
- **When** the tool list is assembled for the review sub-agent
- **Then** `allowed_tools` SHALL contain `write_file`
- **And** `allowed_tools` SHALL NOT contain `edit_file`
- **And** `allowed_tools` SHALL NOT contain any tool not previously present (no removals from the existing list)

### REQ-2: Review verdict SHALL be parseable after sub-agent execution

After the review sub-agent writes `review.md`, `parse_review_verdict` SHALL successfully read the file and return a verdict of `CLEAN` or `ISSUES_FOUND` with associated issues, instead of `UNKNOWN`.

#### Scenario: parse_review_verdict returns a valid verdict

- **Given** `review.md` exists in the change directory with a properly formatted verdict
- **When** `parse_review_verdict` is called
- **Then** the result SHALL be a tuple of `(verdict, issues)` where `verdict` is one of `CLEAN` or `ISSUES_FOUND`
- **And** `verdict` SHALL NOT be `UNKNOWN`
