# Spec: Intent Accuracy Recording in Pipeline

## ADDED Requirements

### Requirement: Intent Decision Recording

The pipeline orchestrator SHALL record every intent classification decision
into the `intent_accuracy` table immediately after `classify()` returns.

#### Scenario: Successful classification is recorded

- **Given** a proposal with non-empty text
- **When** the orchestrator classifies the proposal via `classify()`
- **Then** a row SHALL be inserted into `intent_accuracy` with:
  - `change_name` from the proposal ID
  - `project` from the proposal project
  - `predicted_intent` from `intent.intent_type.value`
  - `confidence` from `intent.confidence`
  - `classification_source` set to `"openspec_override"` when source is `"openspec"`,
    or `"keyword"` / `"llm"` based on which classification path was used
  - `verbalization` from `intent.verbalization`
  - `reasoning` from `intent.reasoning`

#### Scenario: Empty proposal is not recorded

- **Given** a proposal with empty or whitespace-only text
- **When** the orchestrator detects the empty proposal
- **Then** no row SHALL be inserted into `intent_accuracy`
- **And** the change SHALL be skipped

### Requirement: Intent Outcome Updating

The pipeline orchestrator SHALL update the `intent_accuracy` row with
the actual pipeline outcome after the change completes.

#### Scenario: Pipeline succeeds — intent marked correct

- **Given** an intent_accuracy row exists for a change
- **When** the pipeline completes with `outcome == Outcome.SUCCESS`
- **Then** the row SHALL be updated with:
  - `actual_outcome = "success"`
  - `is_correct = 1`

#### Scenario: Pipeline reverts — intent marked incorrect

- **Given** an intent_accuracy row exists for a change
- **When** the pipeline reverts with `outcome == Outcome.REVERTED`
- **Then** the row SHALL be updated with:
  - `actual_outcome = "reverted"`
  - `is_correct = 0`

#### Scenario: Pipeline skips (non-pipeline intent) — intent marked correct

- **Given** an intent_accuracy row exists for a change
- **When** the intent routes to a non-pipeline path (explore, diagnoser, review, ask_user)
- **Then** the row SHALL be updated with:
  - `actual_outcome = "routed"`
  - `is_correct = 1` (routing was successful)

#### Scenario: Sub-agent dispatch outcome is recorded

- **Given** an intent_accuracy row exists for a change routed to a sub-agent
- **When** the sub-agent completes (success or failure)
- **Then** the row SHALL be updated with:
  - `actual_outcome = "success"` or `"failed"` based on sub-agent result
  - `is_correct = 1` if sub-agent returned success, `0` otherwise
