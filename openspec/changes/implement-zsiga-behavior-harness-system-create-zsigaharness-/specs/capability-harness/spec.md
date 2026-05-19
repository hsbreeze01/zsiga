## ADDED Requirements

### Requirement: Intent Router capability test suite
The system SHALL provide a test suite under `zsiga/harness/capability/test_intent_router.py` that validates the `classify()` and `route()` functions from `zsiga.agent.intent_router` across all six IntentType categories (RESEARCH, IMPLEMENTATION, INVESTIGATION, EVALUATION, FIX, OPEN_ENDED). The suite MUST NOT depend on real LLM calls — `_classify_via_llm` SHALL be mocked to return `None` so that keyword-path logic is deterministically exercised.

#### Scenario: Six-category classification coverage
- **GIVEN** a set of >= 20 input messages, at least 3 per IntentType category
- **WHEN** each message is passed to `classify(msg)` with `_classify_via_llm` mocked to return `None`
- **THEN** the returned `Intent.intent_type` SHALL match the expected category for every message

#### Scenario: Construction verb with search keyword disambiguation
- **GIVEN** a proposal text that contains both implementation keywords ("implement", "add") and research keywords ("search", "explore") but describes BUILDING a feature (e.g. "implement search feature for user profiles")
- **WHEN** `classify(msg)` is called
- **THEN** the intent type SHALL be IMPLEMENTATION, not RESEARCH, because implementation keywords with a concrete target object receive a +2 score bonus

#### Scenario: Investigation keyword coverage including "investigate"
- **GIVEN** a message containing "investigate" or "diagnose" or "排查"
- **WHEN** `classify(msg)` is called
- **THEN** the intent type SHALL be INVESTIGATION

#### Scenario: Empty input returns OPEN_ENDED
- **GIVEN** an empty string or whitespace-only message
- **WHEN** `classify(msg)` is called
- **THEN** the intent type SHALL be OPEN_ENDED with confidence >= 0.9

#### Scenario: Route mapping correctness
- **GIVEN** an Intent object for each of the 6 IntentType values
- **WHEN** `route(intent)` is called
- **THEN** the returned string SHALL match: RESEARCH→"dispatch_explore", IMPLEMENTATION→"pipeline", INVESTIGATION→"dispatch_diagnoser", EVALUATION→"dispatch_review", FIX→"pipeline_fix", OPEN_ENDED→"ask_user"

#### Scenario: Verbalization is non-empty for all inputs
- **GIVEN** any non-empty input string
- **WHEN** `classify(msg)` is called
- **THEN** `result.verbalization` SHALL be a non-empty string

### Requirement: Sub-agent dispatch capability test suite
The system SHALL provide a test suite under `zsiga/harness/capability/test_dispatch.py` that validates the `ZsigaOrchestrator._process_change` method routes each IntentType to the correct execution path by mocking the internal dispatch methods and verifying correct call targets.

#### Scenario: RESEARCH intent routes to dispatch_explore
- **GIVEN** a proposal whose text is classified as RESEARCH intent
- **WHEN** `_process_change(prop)` is called on a mocked ZsigaOrchestrator
- **THEN** `_dispatch_explore` SHALL be called and `_run_phases` SHALL NOT be called

#### Scenario: IMPLEMENTATION intent routes to pipeline via _run_phases
- **GIVEN** a proposal whose text is classified as IMPLEMENTATION intent
- **WHEN** `_process_change(prop)` is called
- **THEN** `_run_phases` SHALL be called with `skip_enrich=False`

#### Scenario: FIX intent routes to pipeline with skip_enrich=True
- **GIVEN** a proposal whose text is classified as FIX intent
- **WHEN** `_process_change(prop)` is called
- **THEN** `_run_phases` SHALL be called with `skip_enrich=True`

#### Scenario: INVESTIGATION intent routes to dispatch_diagnoser
- **GIVEN** a proposal whose text is classified as INVESTIGATION intent
- **WHEN** `_process_change(prop)` is called
- **THEN** `_dispatch_diagnoser` SHALL be called and `_run_phases` SHALL NOT be called

#### Scenario: EVALUATION intent routes to dispatch_review
- **GIVEN** a proposal whose text is classified as EVALUATION intent
- **WHEN** `_process_change(prop)` is called
- **THEN** `_dispatch_review` SHALL be called and `_run_phases` SHALL NOT be called

#### Scenario: OPEN_ENDED intent returns False without dispatching
- **GIVEN** a proposal whose text is classified as OPEN_ENDED intent
- **WHEN** `_process_change(prop)` is called
- **THEN** the return value SHALL be False and no dispatch method SHALL be called

### Requirement: Recovery capability test suite
The system SHALL provide a test suite under `zsiga/harness/capability/test_recovery.py` that validates `RecoveryManager` and `EscalationManager` behavior including rollback, fix loop count limits, and escalation abort detection.

#### Scenario: RecoveryManager records failures and triggers rollback after max_failures
- **GIVEN** a RecoveryManager with `max_failures=3` and valid target_path and pre_sha
- **WHEN** `record_failure()` is called 3 times
- **THEN** `should_rollback()` SHALL return True and the 3rd `RecoveryAction.should_rollback` SHALL be True

#### Scenario: EscalationManager escalation levels
- **GIVEN** an EscalationManager with default thresholds (NORMAL < 3, RETRY_DIFFERENT 3-4, NEEDS_HUMAN >= 5)
- **WHEN** `record_failure()` is called N times
- **THEN** `level` SHALL be NORMAL for N < 3, RETRY_DIFFERENT for 3 <= N < 5, NEEDS_HUMAN for N >= 5

#### Scenario: EscalationManager strategy rotation
- **GIVEN** an EscalationManager
- **WHEN** `next_strategy` is checked after 0, 1, 2+ failures
- **THEN** strategy SHALL be SAME after 0 failures, DIFFERENT_APPROACH after 1, SIMPLIFY after 2+

#### Scenario: EscalationManager should_abort after 5 failures
- **GIVEN** an EscalationManager
- **WHEN** `record_failure()` has been called 5 times
- **THEN** `should_abort()` SHALL return True

#### Scenario: RecoveryManager execute_rollback requires target_path and pre_sha
- **GIVEN** a RecoveryManager with `target_path=None` or `pre_sha=None`
- **WHEN** `execute_rollback()` is called
- **THEN** it SHALL return False without attempting git reset

### Requirement: Parallel pool capability test suite
The system SHALL provide a test suite under `zsiga/harness/capability/test_parallel_pool.py` that validates `dispatch_many` and `collect_all` from `zsiga.agent.sub_agent` for concurrent task execution.

#### Scenario: dispatch_many with empty task list returns handle with pending=None
- **GIVEN** an empty task list
- **WHEN** `dispatch_many([])` is called
- **THEN** the returned `PoolHandle.pending` SHALL be None and `collect_all(handle)` SHALL return `[]`

#### Scenario: dispatch_many returns PoolHandle with task count
- **GIVEN** a list of 3 task strings
- **WHEN** `dispatch_many(tasks)` is called
- **THEN** the returned `PoolHandle.tasks` SHALL have length 3

#### Scenario: Individual task failure does not crash collect_all
- **GIVEN** a PoolHandle from dispatch_many where one sub-agent raises an exception
- **WHEN** `collect_all(handle)` is awaited
- **THEN** it SHALL return a list of length equal to the task count, with the failed entry having `success=False`

### Requirement: Self-review capability test suite
The system SHALL provide a test suite under `zsiga/harness/capability/test_reviewer.py` that validates `parse_review_verdict` output parsing for CLEAN, ISSUES_FOUND, and UNKNOWN verdicts.

#### Scenario: parse_review_verdict with CLEAN verdict
- **GIVEN** a review.md file containing "Verdict: CLEAN"
- **WHEN** `parse_review_verdict(change_dir)` is called
- **THEN** it SHALL return `("CLEAN", [])`

#### Scenario: parse_review_verdict with ISSUES_FOUND and issue list
- **GIVEN** a review.md file containing "Verdict: ISSUES_FOUND" followed by numbered issues with severity tags
- **WHEN** `parse_review_verdict(change_dir)` is called
- **THEN** it SHALL return `("ISSUES_FOUND", [list_of_issue_dicts])` where each dict has "severity" and "description" keys

#### Scenario: parse_review_verdict with missing review.md returns UNKNOWN
- **GIVEN** a change directory with no review.md file
- **WHEN** `parse_review_verdict(change_dir)` is called
- **THEN** it SHALL return `("UNKNOWN", [])`

#### Scenario: parse_review_verdict with malformed content returns UNKNOWN
- **GIVEN** a review.md file with no "Verdict:" line
- **WHEN** `parse_review_verdict(change_dir)` is called
- **THEN** it SHALL return `("UNKNOWN", [])`

### Requirement: Skill evolution capability test suite
The system SHALL provide a test suite under `zsiga/harness/capability/test_skill_evolution.py` that validates pattern extraction from learnings and skill markdown generation via `evolve_skills`.

#### Scenario: Recurring patterns extracted from learnings
- **GIVEN** a learnings.jsonl with >= 3 entries sharing the same `pattern_key`
- **WHEN** `mine_patterns(min_occurrences=3)` is called with that path
- **THEN** the returned list SHALL contain a Pattern with matching key and count >= 3

#### Scenario: evolve_skills generates markdown files
- **GIVEN** sufficient learnings data with recurring patterns
- **WHEN** `evolve_skills(min_cluster_occurrences=2)` is called with a temp skills_dir
- **THEN** markdown files SHALL be created in skills_dir with YAML frontmatter containing `auto_generated: true`

#### Scenario: evolve_skills skips hand-written skill files
- **GIVEN** a skills_dir containing a .md file without `auto_generated: true`
- **WHEN** `evolve_skills()` generates a skill for the same cluster prefix
- **THEN** the hand-written file SHALL NOT be overwritten
