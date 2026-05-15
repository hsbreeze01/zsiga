# Spec: Autonomous Sense — Value Judgment and Proposal Generation

## ADDED Requirements

### REQ-JUDGE-001: Priority Assessment

The system SHALL assign a priority level to each Signal based on its type and severity.

#### Scenario: Health check failure → HIGH
- Given a Signal with `type=health_check` and `severity=HIGH`
- When the judge evaluates it
- Then the JudgeResult SHALL have `priority=HIGH`

#### Scenario: Log error with critical keyword → CRITICAL
- Given a Signal with `type=log_errors` and the error contains "OOM" or "disk full" or "OutOfMemory"
- When the judge evaluates it
- Then the JudgeResult SHALL have `priority=CRITICAL`

#### Scenario: Git changes with no issues → LOW
- Given a Signal with `type=git_changes` and commits are normal feature work
- When the judge evaluates it
- Then the JudgeResult SHALL have `priority=LOW`

### REQ-JUDGE-002: Deduplication

The system SHALL not propose the same issue within the dedup window (default 24h).
Dedup key SHALL be computed as `{signal_type}:{project}:{normalized_data_hash}`.

#### Scenario: Duplicate signal within 24h
- Given a Signal with dedup key `health_check:compass:api-strategy-groups-500` was already proposed at T0
- When the same Signal is detected at T0+2h
- Then the Signal SHALL be filtered out (no JudgeResult produced)

#### Scenario: Same issue after 24h
- Given a Signal with dedup key `health_check:compass:api-strategy-groups-500` was proposed at T0
- When the same Signal is detected at T0+25h
- Then the Signal SHALL pass dedup and produce a JudgeResult

### REQ-JUDGE-003: Rate Limiting

The system SHALL limit proposals to `max_proposals_per_cycle` (default 3) per cycle, sorted by priority.

#### Scenario: More signals than limit
- Given 5 Signals pass dedup and filtering
- And `max_proposals_per_cycle=3`
- When the judge ranks them by priority
- Then only the top 3 (highest priority) SHALL produce JudgeResults

### REQ-JUDGE-004: Min Priority Filter

The system SHALL discard Signals below `min_priority` (default MEDIUM).

#### Scenario: LOW priority below threshold
- Given `min_priority=MEDIUM`
- And a Signal evaluates to `priority=LOW`
- When the judge processes it
- Then the Signal SHALL be discarded

### REQ-PROPOSE-001: Proposal Generation

The system SHALL use the LLM agent to generate a proposal.md from a JudgeResult.
The proposal SHALL conform to OpenSpec format and include sense metadata.

#### Scenario: Successful proposal generation
- Given a JudgeResult with `signal.type=health_check`, `project=compass`
- And the project context is available from `build_project_context()`
- When the proposer runs
- Then a `proposal.md` SHALL be written to `{target_path}/openspec/changes/{slug}/`
- And the proposal SHALL contain `## Meta` section with `signal_source`, `detected_at`, `signal_priority`

#### Scenario: Slug collision
- Given a proposal with slug `fix-health-check` already exists in the target
- When the proposer tries to create the same slug
- Then the proposer SHALL append a numeric suffix (e.g., `fix-health-check-2`)

### REQ-PROPOSE-002: Sense History Recording

The system SHALL record each proposed Signal to `sense_history.jsonl`.

#### Scenario: Record after proposal
- Given a JudgeResult produces a proposal
- When the proposal is written
- Then an entry SHALL be appended to `sense_history.jsonl`
- And the entry SHALL contain `ts`, `signal_type`, `project`, `key` (dedup key), `action=proposed`, `proposal_id`

#### Scenario: Record after skip (dedup)
- Given a Signal is filtered by dedup
- When the judge skips it
- Then an entry SHALL be appended with `action=skipped`, `reason=dedup`

### REQ-CYCLE-001: Sense Phase Integration

The `run_cycle()` method SHALL execute the sense phase before the existing pipeline phase.

#### Scenario: Sense enabled
- Given `sense.enabled=true`
- When `run_cycle()` is called
- Then sense → judge → propose SHALL run first
- And any generated proposals SHALL be available for the existing scanner.scan()

#### Scenario: Sense disabled
- Given `sense.enabled=false`
- When `run_cycle()` is called
- Then the sense phase SHALL be skipped entirely
- And the cycle SHALL proceed directly to the existing pipeline
