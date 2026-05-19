## ADDED Requirements

### Requirement: Budget resilience test suite
The system SHALL provide tests verifying TokenBudget behavior under extreme conditions: zero budget, per-turn overflow, phase isolation, and compaction pressure.

#### Scenario: Phase budget isolation
- **WHEN** set_phase("impl") is called after ENRICH consumed >= 500k tokens
- **THEN** budget._used SHALL be 0, allowing IMPLEMENT full 600k budget

#### Scenario: Zero total budget
- **WHEN** TokenBudget is initialized with total_budget=0
- **THEN** the first record() call SHALL return session_exceeded=True without crashing

#### Scenario: Per-turn limit enforcement
- **WHEN** a single LLM call returns completion_tokens > per_turn_limit
- **THEN** the run loop SHALL stop with BUDGET_EXCEEDED result

#### Scenario: Compaction triggers under context pressure
- **WHEN** messages token estimate exceeds compaction_threshold * compaction_ratio
- **THEN** should_compact SHALL return True

### Requirement: Intent adversarial test suite
The system SHALL provide tests with deliberately constructed adversarial inputs designed to trigger misclassification.

#### Scenario: Triple category keyword collision
- **WHEN** input contains keywords from 3+ categories (e.g. "implement investigate module for debugging search errors")
- **THEN** implementation SHALL win due to base weight advantage

#### Scenario: Keyword stuffing attack
- **WHEN** input is "explore explore explore implement"
- **THEN** implementation SHALL be classified (last construction verb is the true intent)

#### Scenario: Nested clause disambiguation
- **WHEN** input is "I want to understand how to build a search feature"
- **THEN** classification SHALL be IMPLEMENTATION (the action is building, not understanding)

#### Scenario: Chinese mixed with English technical terms
- **WHEN** input is "修复 search 功能的 bug：搜索不到结果"
- **THEN** classification SHALL be FIX (修复/bug keywords dominate)

### Requirement: Tool error handling test suite
The system SHALL provide tests verifying graceful behavior when tools fail or return unexpected results.

#### Scenario: File read on non-existent path
- **WHEN** read_file is called with a path that does not exist
- **THEN** the function SHALL return empty string or None, not raise an exception

#### Scenario: Git command failure on detached HEAD
- **WHEN** git_ops.rev_parse is called on a repo with no commits
- **THEN** the function SHALL return a fallback value or raise a catchable error
