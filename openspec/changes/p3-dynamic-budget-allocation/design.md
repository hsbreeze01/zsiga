# Design: P3 Dynamic Budget Allocation

## Architecture Decision

**One budget per change, not per phase.** The current `AgentLoop` holds a single
`TokenBudget` instance that is reset per-phase via `set_phase()`. We keep this
pattern: before the first phase of a change, the orchestrator updates
`budget.total_budget` to the selected profile's value. All subsequent phases
within that change share the same profile's budget limit.

**Profile selection is rule-based, not ML-based.** Four simple rules in
priority order (cross-project → self_modify → fix → implementation) keep the
logic deterministic and testable. The intent type is already resolved by
`IntentRouter`, and the project name / cross-project flag are available in the
orchestrator.

## Data Flow

```
zsiga.yaml
  pipeline.budget_profiles:
    fix:       { total_budget: 300000 }
    implementation: { total_budget: 600000 }
    cross_project:  { total_budget: 200000 }
    self_modify:    { total_budget: 800000 }
         │
         ▼
  config.py  →  BudgetProfileConfig (dict of name → total_budget)
         │
         ▼
  orchestrator._process_change()
    1. intent = classify(proposal_text)
    2. profile_name = select_budget_profile(intent_type, project, is_cross_project)
    3. profile_budget = config.pipeline.budget_profiles[profile_name]
    4. agent.budget.total_budget = profile_budget   ← before any phase runs
    5. rec.budget_profile = profile_name             ← stored in ChangeRecord
         │
         ▼
  collector.compute_stats()
    → budget_profile_stats: { "fix": { count, avg_tokens }, ... }
```

## Files to Modify / Create

| File | Change |
|------|--------|
| `zsiga/config.py` | Add `BudgetProfileConfig` dataclass; parse `pipeline.budget_profiles` from yaml |
| `zsiga/agent/token_budget.py` | Add `select_budget_profile()` function |
| `zsiga/pipeline/orchestrator.py` | Call `select_budget_profile()` in `_process_change()`; set budget before phases |
| `zsiga/metrics/types.py` | Add `budget_profile: str` field to `ChangeRecord` |
| `zsiga/metrics/collector.py` | Compute `budget_profile_stats` in `compute_stats()` |
| `tests/test_token_budget.py` | Add tests for `select_budget_profile()` and config parsing |
| `zsiga.yaml` | Add `budget_profiles` section under `pipeline` |

## Backward Compatibility

- If `pipeline.budget_profiles` is absent, defaults are used (identical to
  current flat 600K for implementation, new values for other types).
- `ChangeRecord.budget_profile` defaults to `""` — old records without it
  are gracefully handled by `compute_stats()`.
- No API signature changes to `AgentLoop` or `TokenBudget`.
