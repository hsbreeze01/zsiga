# Delta Spec: Review Phase Metrics Recording

## ADDED Requirements

### Requirement: Review PhaseRecord SHALL capture LLM usage metrics

The review phase (Phase 2.5) in the pipeline orchestrator SHALL record
`llm_calls`, `tool_calls`, `prompt_tokens`, and `completion_tokens` in its
`PhaseRecord`, just as all other phases do (implement, verify, enrich).

#### Scenario: Review sub-agent completes a review round

- Given a running pipeline with `review_max_rounds >= 1`
- When the review sub-agent executes and produces a `SubAgentResult`
- Then the orchestrator SHALL extract `llm_calls`, `tool_calls`,
  `prompt_tokens`, and `completion_tokens` from the accumulated review
  loop result
- And the review `PhaseRecord` SHALL include these values

#### Scenario: Review loop executes fix attempt

- Given a review round that finds CRITICAL issues
- When the orchestrator's main agent runs a fix attempt via `agent.run()`
- Then the `RunResult` metrics SHALL be accumulated into the review loop
  totals
- And the final `PhaseRecord` SHALL include these fix-turn metrics

### Requirement: ReviewLoopResult SHALL carry accumulated metrics

The `ReviewLoopResult` dataclass SHALL include fields for
`llm_calls`, `tool_calls`, `prompt_tokens`, and `completion_tokens`
that accumulate across all review rounds and fix attempts.

#### Scenario: Multiple review rounds with fix attempts

- Given `review_max_rounds = 2`
- When round 1 produces 5 LLM calls / 12 tool calls, and a fix attempt
  produces 3 LLM calls / 4 tool calls
- And round 2 produces 4 LLM calls / 8 tool calls
- Then `ReviewLoopResult.llm_calls` SHALL be 12
- And `ReviewLoopResult.tool_calls` SHALL be 24

### Requirement: run_review_loop SHALL capture SubAgentResult metrics

`run_review_loop` SHALL NOT discard the `SubAgentResult` returned by
`run_review`. It SHALL accumulate the metrics from each review
sub-agent execution.

#### Scenario: Single review round returns CLEAN

- Given `review_max_rounds = 1`
- When `run_review` returns a `SubAgentResult` with `llm_calls=6`,
  `tool_calls=10`, `prompt_tokens=8000`, `completion_tokens=2000`
- Then the `ReviewLoopResult` SHALL contain those same metric values

### Requirement: run_review_loop SHALL capture fix RunResult metrics

When the review loop triggers a fix attempt using the main agent,
the resulting `RunResult` metrics SHALL be accumulated into the
loop totals.

#### Scenario: Fix attempt after CRITICAL issues

- Given a review round that finds CRITICAL issues
- When `agent.run()` for the fix returns a `RunResult` with
  `llm_calls=4`, `tool_calls=6`, `prompt_tokens=5000`,
  `completion_tokens=1500`
- Then these values SHALL be added to the accumulated loop metrics
