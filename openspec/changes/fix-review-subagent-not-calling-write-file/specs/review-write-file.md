# Delta Spec: Review Sub-Agent Must Write review.md via Tool Call

## MODIFIED Requirements

### Requirement: Review prompt SHALL enforce write_file tool usage

The `run_review()` function's user prompt SHALL include an explicit, unambiguous instruction that the sub-agent MUST call the `write_file` tool to persist the review output to `{change_dir}/review.md`. The prompt SHALL state that outputting review content as plain text in the reply is insufficient.

#### Scenario: LLM receives explicit write_file instruction

- **Given** a review sub-agent is invoked for a change directory
- **When** the user prompt is constructed
- **Then** the prompt SHALL contain a directive equivalent to "You MUST call the write_file tool to write the review result to {change_dir}/review.md. Do NOT output the review content only in your reply text."
- **And** the directive SHALL appear in a prominent position (beginning or end) of the user prompt

#### Scenario: Review prompt does not rely on implicit tool usage

- **Given** the existing review prompt wording
- **When** the new prompt is constructed
- **Then** the instruction to use write_file SHALL NOT be phrased as a suggestion (e.g., "please write to...") but as a mandatory action (e.g., "You MUST call write_file...")

### Requirement: run_review SHALL defensively persist review content if sub-agent omits write_file

After the review sub-agent returns a `SubAgentResult`, `run_review()` SHALL check whether `{change_dir}/review.md` exists on disk. If the file does not exist AND `SubAgentResult.content` contains a line matching `Verdict:`, the function SHALL write the content to `{change_dir}/review.md` automatically.

#### Scenario: Sub-agent calls write_file correctly

- **Given** a review sub-agent that calls write_file and creates `{change_dir}/review.md`
- **When** `run_review()` processes the SubAgentResult
- **Then** the function SHALL NOT overwrite or duplicate the file
- **And** SHALL proceed normally

#### Scenario: Sub-agent omits write_file but content contains Verdict

- **Given** a review sub-agent that returns content with a `Verdict:` line but did not call write_file
- **When** `run_review()` checks for `{change_dir}/review.md` and finds it missing
- **Then** `run_review()` SHALL write `SubAgentResult.content` to `{change_dir}/review.md`
- **And** `parse_review_verdict` SHALL subsequently succeed in reading the file

#### Scenario: Sub-agent returns content without Verdict and file missing

- **Given** a review sub-agent that returns content without a `Verdict:` line and did not create the file
- **When** `run_review()` checks for `{change_dir}/review.md`
- **Then** the function SHALL NOT create the file (no Verdict means nothing useful to persist)
- **And** `parse_review_verdict` SHALL return UNKNOWN as before

## Constraints

- This change SHALL NOT modify `roles.py` `allowed_tools` configuration
- This change SHALL NOT modify `parse_review_verdict` logic
- This change SHALL NOT modify metrics recording logic
- All existing tests in `tests/test_reviewer.py` SHALL continue to pass
