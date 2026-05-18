# Delta Spec: Token Budget Manager

## ADDED Requirements

### REQ-BUDGET-001: TokenBudget tracking

The system SHALL provide a `TokenBudget` class that tracks cumulative token usage (prompt tokens and completion tokens) across all LLM calls within a single agent run session.

#### Scenario: Record token usage from an LLM response
- **Given** a TokenBudget instance initialized with a total session limit of 200000 tokens
- **When** the agent records usage of 5000 prompt tokens and 800 completion tokens from a single LLM call
- **Then** the budget SHALL report total used as 5800 tokens
- **And** the budget SHALL report remaining as 194200 tokens

#### Scenario: Accumulate usage across multiple LLM calls
- **Given** a TokenBudget with any limit
- **When** the agent records (prompt=4000, completion=500) then (prompt=6000, completion=1200) across two turns
- **Then** the budget SHALL report total used as 11700 tokens

### REQ-BUDGET-002: Per-turn token limit

The system SHALL enforce a per-turn token limit. When the completion tokens of a single LLM response exceed the per-turn limit, the agent loop SHALL stop and return a `BUDGET_EXCEEDED` result.

#### Scenario: Single turn exceeds per-turn limit
- **Given** a TokenBudget with per_turn_limit=4096
- **When** an LLM response returns 5000 completion tokens
- **Then** the budget SHALL flag the turn as exceeded
- **And** the agent loop SHALL return RunResult with content "BUDGET_EXCEEDED"

#### Scenario: Single turn within per-turn limit
- **Given** a TokenBudget with per_turn_limit=4096
- **When** an LLM response returns 3000 completion tokens
- **Then** the budget SHALL NOT flag the turn as exceeded

### REQ-BUDGET-003: Total session budget enforcement

The system SHALL enforce a total session token budget. When cumulative usage exceeds the session budget, the agent loop SHALL stop and return a `BUDGET_EXCEEDED` result.

#### Scenario: Cumulative usage exceeds session budget
- **Given** a TokenBudget with total_budget=10000
- **When** cumulative usage reaches 10500 tokens after recording a response
- **Then** the budget SHALL flag the session as exceeded
- **And** the agent loop SHALL return RunResult with content "BUDGET_EXCEEDED"

#### Scenario: Session budget not yet reached
- **Given** a TokenBudget with total_budget=100000
- **When** cumulative usage is 80000 tokens
- **Then** the budget SHALL NOT flag the session as exceeded

### REQ-BUDGET-004: Proactive compaction trigger

The system SHALL trigger compaction proactively when the estimated message token count approaches the compaction threshold, using a configurable ratio. This replaces the fixed-interval (`turn % 3`) compaction trigger.

The `should_compact` method SHALL return True when:
- `estimated_tokens(messages) >= threshold * compaction_ratio` (default ratio 0.8)

#### Scenario: Compaction triggered when approaching threshold
- **Given** compaction threshold of 60000 tokens and compaction_ratio of 0.8
- **When** estimated message tokens reach 49000 (>= 60000 * 0.8 = 48000)
- **Then** the budget SHALL signal that compaction should be performed

#### Scenario: Compaction not triggered when well below ratio
- **Given** compaction threshold of 60000 tokens and compaction_ratio of 0.8
- **When** estimated message tokens are 40000 (< 48000)
- **Then** the budget SHALL NOT signal compaction

### REQ-BUDGET-005: Budget configuration via zsiga.yaml

The token budget parameters SHALL be configurable through the `pipeline.compaction` section of `zsiga.yaml`, with sensible defaults when not specified.

Configuration keys (all optional):
- `total_budget`: int, default 200000 — maximum total tokens per session
- `per_turn_limit`: int, default 8192 — maximum completion tokens per single LLM call
- `compaction_ratio`: float, default 0.8 — fraction of threshold at which proactive compaction triggers

#### Scenario: Default values applied when config keys absent
- **Given** a zsiga.yaml with no `total_budget`, `per_turn_limit`, or `compaction_ratio` keys
- **When** the config is loaded
- **Then** CompactionConfig SHALL have total_budget=200000, per_turn_limit=8192, compaction_ratio=0.8

#### Scenario: Custom values loaded from config
- **Given** a zsiga.yaml with `compaction.total_budget: 150000` and `compaction.per_turn_limit: 4096`
- **When** the config is loaded
- **Then** CompactionConfig SHALL have total_budget=150000, per_turn_limit=4096

### REQ-BUDGET-006: Budget state reporting

The TokenBudget SHALL provide a snapshot method that returns the current budget state for logging and dashboard display.

#### Scenario: Snapshot returns budget state
- **Given** a TokenBudget with total_budget=100000, per_turn_limit=4096
- **When** 35000 tokens have been used
- **Then** the snapshot SHALL include: total_budget=100000, used=35000, remaining=65000, usage_ratio=0.35

## MODIFIED Requirements

### REQ-BUDGET-M001: AgentLoop compaction trigger

The AgentLoop `run` method SHALL replace the fixed-interval compaction trigger (`turn % 3 == 0`) with TokenBudget's `should_compact` method. Compaction SHALL be triggered when the budget signals it, regardless of turn number.

#### Scenario: Compaction triggers based on budget, not turn count
- **Given** an AgentLoop with TokenBudget enabled and compaction_ratio=0.8, threshold=60000
- **When** on turn 2 (not a multiple of 3) estimated tokens reach 50000
- **Then** compaction SHALL be triggered

#### Scenario: Compaction skipped when budget says no
- **Given** an AgentLoop with TokenBudget enabled and compaction_ratio=0.8, threshold=60000
- **When** on turn 3 estimated tokens are only 30000
- **Then** compaction SHALL be skipped

### REQ-BUDGET-M002: AgentLoop budget enforcement loop

The AgentLoop `run` method SHALL check token budget after each LLM response. If the budget is exceeded (per-turn or session), the loop SHALL return `BUDGET_EXCEEDED` immediately.

#### Scenario: Loop stops on session budget exceeded
- **Given** an AgentLoop with total_budget=5000
- **When** cumulative token usage exceeds 5000 after an LLM response on turn 5
- **Then** the loop SHALL return RunResult("BUDGET_EXCEEDED", ...) with the current token counts

#### Scenario: Loop stops on per-turn budget exceeded
- **Given** an AgentLoop with per_turn_limit=2048
- **When** a single LLM response returns 3000 completion tokens
- **Then** the loop SHALL return RunResult("BUDGET_EXCEEDED", ...) with the current token counts
