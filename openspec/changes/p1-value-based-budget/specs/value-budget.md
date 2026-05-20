# Spec: Value-Based Budget — Stale Detection + Soft Cutoff

## ADDED Requirements

### REQ-VBB-001: Per-Turn Budget Usage Recording

The system SHALL record token usage for every LLM turn into a persistent `budget_usage` database table with the following columns:

- `id` (INTEGER PRIMARY KEY)
- `change_name` (TEXT)
- `phase` (TEXT)
- `turn_number` (INTEGER)
- `prompt_tokens` (INTEGER)
- `completion_tokens` (INTEGER)
- `cumulative_used` (INTEGER)
- `budget_limit` (INTEGER)
- `value_signal` (TEXT — one of: `productive`, `stale`, `extended`)
- `created_at` (TEXT)

#### Scenario: Record a productive turn

- **Given** an agent loop is running for change `c1` in phase `impl`
- **When** turn 3 completes with 2000 prompt tokens and 800 completion tokens (cumulative 15000)
- **Then** a row is inserted into `budget_usage` with `change_name=c1`, `phase=impl`, `turn_number=3`, `prompt_tokens=2000`, `completion_tokens=800`, `cumulative_used=15000`, `value_signal=productive`

#### Scenario: Record a stale turn

- **Given** an agent loop is running and the last N turns produced no value signals
- **When** the turn completes and is classified as stale
- **Then** the `value_signal` column SHALL be `stale`

---

### REQ-VBB-002: Value Signal Detection

The system SHALL classify each completed turn as **productive** or **stale** based on observable tool-call outcomes within that turn.

A turn is **productive** if ANY of the following occurred:
- A file was written (`write_file` or `edit_file` tool called)
- A test passed (bash tool returned exit_code 0 for a test command)
- Lint was clean (bash tool returned exit_code 0 for a lint command)
- A task was checked off in tasks.md

A turn is **stale** if none of the above occurred.

The system SHALL maintain a **consecutive stale counter** that resets to 0 on any productive turn and increments by 1 on each stale turn.

#### Scenario: Productive turn after stale streak

- **Given** consecutive stale counter is 3
- **When** the current turn calls `write_file`
- **Then** the counter resets to 0 and the turn is classified as `productive`

#### Scenario: Stale turn increments counter

- **Given** consecutive stale counter is 2
- **When** the current turn completes with only `read_file` and `search` tool calls (no file writes, no test/lint success)
- **Then** the counter becomes 3 and the turn is classified as `stale`

---

### REQ-VBB-003: Stale-Limit Stop Condition

The system SHALL stop the current phase immediately when the consecutive stale counter reaches `stale_limit` (default: 5, configurable).

When stopped by stale-limit, the `RunResult.content` SHALL be `STALE_LIMIT`.

#### Scenario: Stop after stale limit reached

- **Given** `stale_limit=3` and consecutive stale counter is 2
- **When** the next turn is classified as stale (counter becomes 3)
- **Then** the agent loop returns `RunResult(content="STALE_LIMIT", ...)` immediately

#### Scenario: Stale limit not reached with productive turns

- **Given** `stale_limit=5` and consecutive stale counter is 4
- **When** the next turn calls `edit_file`
- **Then** the counter resets to 0 and the loop continues normally

---

### REQ-VBB-004: Soft Budget Extension

When cumulative token usage exceeds `total_budget` but the last turn was **productive**, the system SHALL extend the effective budget to `min(total_budget * 1.5, total_budget + budget_extend_margin)` instead of stopping immediately.

The system SHALL NOT extend beyond 1.5× the original budget under any condition.

When the session truly exceeds the extended budget, the `RunResult.content` SHALL be `BUDGET_EXCEEDED` as before.

#### Scenario: Budget exceeded but producing value → extend

- **Given** `total_budget=200000`, `budget_extend_margin=100000`, cumulative used is 201000
- **When** the last turn was productive (file written)
- **Then** the effective budget becomes `min(300000, 300000) = 300000` and the loop continues

#### Scenario: Extended budget also exceeded → stop

- **Given** `total_budget=200000`, cumulative used is 310000 (extended limit was 300000)
- **When** the next LLM call completes
- **Then** the loop returns `RunResult(content="BUDGET_EXCEEDED", ...)`

#### Scenario: Budget exceeded and not producing value → stop immediately

- **Given** `total_budget=200000`, cumulative used is 201000
- **When** the last turn was stale (no file edits, no test pass)
- **Then** the loop returns `RunResult(content="BUDGET_EXCEEDED", ...)` without extension

---

### REQ-VBB-005: Budget Analytics API

The system SHALL provide a `compute_budget_stats()` function that returns a dictionary with:

- `per_change`: list of `{change_name, total_tokens, turns, stale_ratio, phases}` for each change
- `phase_distribution`: dict of `{phase_name: {total_tokens, avg_per_turn, turn_count}}`
- `overall_stale_ratio`: float (total stale turns / total turns)

#### Scenario: Analytics computed from recorded data

- **Given** `budget_usage` table has 20 rows across 2 changes
- **When** `compute_budget_stats()` is called
- **Then** the result contains `per_change` with 2 entries and correct `stale_ratio` per change

---

## MODIFIED Requirements

### REQ-VBB-006: Budget Enforcement in Agent Loop

The existing `BUDGET_EXCEEDED` hard stop in `AgentLoop.run()` SHALL be replaced with the value-based logic defined in REQ-VBB-003 and REQ-VBB-004.

The `record()` method on `TokenBudget` SHALL be extended to return `value_signal` and `stale_count` in its status dict.

The `set_phase()` method on `AgentLoop` SHALL reset the consecutive stale counter to 0 (in addition to resetting `_used`).

#### Scenario: Loop integrates stale detection

- **Given** an agent loop with `stale_limit=3`
- **When** 3 consecutive stale turns occur
- **Then** the loop returns `STALE_LIMIT` instead of continuing to the max turn count

#### Scenario: Loop integrates soft budget extension

- **Given** an agent loop with `total_budget=100000`
- **When** cumulative usage reaches 105000 and the last turn was productive
- **Then** the effective budget is extended and the loop continues (does not return `BUDGET_EXCEEDED`)
