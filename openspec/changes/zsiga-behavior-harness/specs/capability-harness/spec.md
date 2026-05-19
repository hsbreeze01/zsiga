## ADDED Requirements

### Requirement: Intent Router capability test suite
The system SHALL provide a test suite that validates intent classification for all six IntentType categories with >= 20 test cases covering normal classification, disambiguation (construction vs passive), Chinese/English mixed input, and empty/ambiguous edge cases.

#### Scenario: Construction verb with search keyword disambiguation
- **WHEN** proposal text contains both implementation keywords ("implement", "add") and research keywords ("search", "explore") describing BUILDING a feature
- **THEN** the intent router SHALL classify as IMPLEMENTATION, not RESEARCH

#### Scenario: Pure research question
- **WHEN** proposal text is a question like "how does X work" or "查看一下 token budget 的实现"
- **THEN** the intent router SHALL classify as RESEARCH

#### Scenario: Fix intent with mixed keywords
- **WHEN** proposal text starts with fix/修复 followed by a description containing search/explore words
- **THEN** the intent router SHALL classify as FIX

#### Scenario: Empty input handling
- **WHEN** proposal text is empty string or whitespace only
- **THEN** the intent router SHALL classify as OPEN_ENDED with confidence >= 0.4

#### Scenario: Investigation keyword coverage
- **WHEN** proposal text contains "investigate", "diagnose", or "排查"
- **THEN** the intent router SHALL classify as INVESTIGATION

### Requirement: Sub-agent dispatch capability test suite
The system SHALL provide a test suite that validates the orchestrator routes each IntentType to the correct execution path (dispatch_explore, dispatch_diagnoser, dispatch_review, pipeline, pipeline_fix, ask_user).

#### Scenario: RESEARCH intent routes to dispatch_explore
- **WHEN** intent is classified as RESEARCH
- **THEN** the orchestrator SHALL call `_dispatch_explore` and NOT enter the pipeline

#### Scenario: IMPLEMENTATION intent routes to pipeline
- **WHEN** intent is classified as IMPLEMENTATION
- **THEN** the orchestrator SHALL call `_run_phases` with skip_enrich=False

#### Scenario: FIX intent routes to pipeline with skip_enrich
- **WHEN** intent is classified as FIX
- **THEN** the orchestrator SHALL call `_run_phases` with skip_enrich=True

### Requirement: Recovery capability test suite
The system SHALL provide a test suite that validates RecoveryManager rollback behavior and EscalationManager abort detection.

#### Scenario: Mechanical verification failure triggers fix loop
- **WHEN** implement phase produces code that fails lint or test
- **THEN** the orchestrator SHALL attempt fix loop up to max_attempts before reverting

#### Scenario: Escalation abort prevents infinite retry
- **WHEN** escalation.should_abort() returns True after repeated failures
- **THEN** the orchestrator SHALL revert and stop, not attempt further fixes

### Requirement: Parallel pool capability test suite
The system SHALL provide a test suite that validates dispatch_many/collect_all concurrent execution.

#### Scenario: Multiple explore tasks run concurrently
- **WHEN** derive_explore_tasks returns N tasks and dispatch_many is called
- **THEN** collect_all SHALL return N results within timeout, with individual task failure not blocking others

### Requirement: Self-review capability test suite
The system SHALL provide a test suite that validates run_review execution and parse_review_verdict output parsing.

#### Scenario: Review verdict CLEAN parsed correctly
- **WHEN** run_review completes and writes verdict.md with "CLEAN"
- **THEN** parse_review_verdict SHALL return ("CLEAN", [])

#### Scenario: Review verdict with issues
- **WHEN** run_review completes and writes verdict.md with issues list
- **THEN** parse_review_verdict SHALL return (verdict, [issue_dicts]) with severity and description fields

### Requirement: Skill evolution capability test suite
The system SHALL provide a test suite that validates pattern extraction from learnings and rule generation.

#### Scenario: Recurring pattern extracted from learnings
- **WHEN** learnings.jsonl contains >= 2 entries with same pattern_key
- **THEN** the skill evolver SHALL generate a rule that addresses the pattern
