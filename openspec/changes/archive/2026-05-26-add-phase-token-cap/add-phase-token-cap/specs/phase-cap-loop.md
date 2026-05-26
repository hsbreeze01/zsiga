# Spec: Phase Token Cap — AgentLoop CAP_EXCEEDED Signal

## MODIFIED Requirements

### Requirement: AgentLoop detects phase cap exceeded

When `budget.record()` returns `cap_exceeded: True`, the `AgentLoop.run()`
method SHALL terminate the current loop iteration and return a `RunResult`
with `content="CAP_EXCEEDED"`.  This is a soft termination — it indicates
the phase hit its token ceiling, not that the session ran out of budget.

The `CAP_EXCEEDED` check SHALL occur inside the existing budget-enforcement
block (after recording token usage from `resp.usage`) and AFTER the
`session_exceeded` check, so that when both conditions are true,
`BUDGET_EXCEEDED` takes precedence (hard limit overrides soft limit).

The `CAP_EXCEEDED` check SHALL only trigger when `budget.record()` returns
`cap_exceeded: True` — the loop SHALL NOT duplicate the `phase_cap > 0`
check itself; it relies entirely on the budget object's computation.

#### Scenario: Loop returns CAP_EXCEEDED when phase cap exceeded

- **testable**: false
- **Given** an `AgentLoop` whose `budget` has `phase_cap=100` and `_used=90`
- **When** the loop processes an LLM response with `prompt_tokens=20,
  completion_tokens=10` (total 30, pushing usage to 120 > cap 100)
- **Then** the loop SHALL return a `RunResult` with `content="CAP_EXCEEDED"`

#### Scenario: BUDGET_EXCEEDED takes precedence over CAP_EXCEEDED

- **testable**: false
- **Given** an `AgentLoop` whose `budget` has `total_budget=100, phase_cap=50`
  and `_used=40`
- **When** the loop processes an LLM response that pushes usage above both
  limits
- **Then** the loop SHALL return `content="BUDGET_EXCEEDED"` (not
  `CAP_EXCEEDED`)

#### Scenario: CAP_EXCEEDED does not trigger on normal usage

- **testable**: false
- **Given** an `AgentLoop` whose `budget` has `phase_cap=500` and `_used=100`
- **When** the loop processes an LLM response with `prompt_tokens=50,
  completion_tokens=30` (total 80, cumulative 180 < cap 500)
- **Then** the loop SHALL continue normally and NOT return `CAP_EXCEEDED`

#### Scenario: CAP_EXCEEDED RunResult includes accurate token counts

- **testable**: false
- **Given** an `AgentLoop` that terminates with `CAP_EXCEEDED`
- **When** the `RunResult` is examined
- **Then** it SHALL contain accurate `prompt_tokens` and `completion_tokens`
  reflecting the total usage up to and including the terminating LLM call
