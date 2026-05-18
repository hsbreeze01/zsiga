# Design: agent/recovery.py — Failure Recovery Protocol

## Architecture Decision

Create a new `zsiga/agent/recovery.py` module that encapsulates the full failure recovery lifecycle as a single `RecoveryManager` class. This module **wraps and enhances** the existing `EscalationManager` (from `agent/escalation.py`) and `Diagnoser` (from `pipeline/diagnoser.py`), providing a unified entry point for:

1. Failure tracking (delegated to `EscalationManager`)
2. Auto-rollback decision + execution (new logic + `git_ops.reset_hard`)
3. Root cause analysis (delegated to `pipeline.diagnoser.Diagnoser`)
4. Strategy rotation (delegated to `EscalationManager.next_strategy`)
5. Diagnostic report generation (new logic, replaces ad-hoc `_handle_escalation_abort`)
6. Lesson recording (delegated to `memory.learn`)

**Why not modify `escalation.py` directly?** The existing `EscalationManager` is a pure escalation tracker. The recovery module adds git operations, diagnosis orchestration, and report persistence — responsibilities that belong at a higher level. Keeping them separate preserves the single-responsibility of `EscalationManager`.

## Data Flow

```
Orchestrator (_fix_loop / _eval_fix_loop)
  │
  ├─ failure occurs
  │     │
  │     ▼
  │  RecoveryManager.record_failure(error, phase)
  │     │
  │     ├─ EscalationManager.record_failure() → track failure
  │     │
  │     ├─ Diagnoser.diagnose() → RCAReport (root cause analysis)
  │     │
  │     └─ return RecoveryAction { strategy, should_rollback, hint }
  │
  ├─ if RecoveryAction.should_rollback:
  │     │
  │     ▼
  │  RecoveryManager.execute_rollback()
  │     │
  │     ├─ git_ops.reset_hard(target_path, pre_sha, transport)
  │     ├─ record_lesson(pattern_key="pipeline.fail.rollback")
  │     └─ return True
  │
  ├─ if all strategies exhausted:
  │     │
  │     ▼
  │  RecoveryManager.generate_diagnostic_report()
  │     │
  │     ├─ compose markdown from failures + RCA
  │     ├─ save to {change_dir}/recovery-report.md
  │     └─ record_lesson(pattern_key="pipeline.fail.recovery")
  │
  └─ else: use RecoveryAction.strategy + hint in next fix attempt
```

## New Types

```python
# In zsiga/agent/recovery.py

@dataclass
class RecoveryAction:
    """Returned by record_failure() — tells orchestrator what to do next."""
    strategy: Strategy           # SAME / DIFFERENT_APPROACH / SIMPLIFY
    strategy_hint: str           # prompt modifier for fix engine
    should_rollback: bool        # whether to git reset --hard
    attempt: int                 # current attempt number
    rca_report: DiagnosisReport | None  # root cause analysis result

@dataclass
class RecoveryReport:
    """Full diagnostic report written on strategy exhaustion."""
    change_name: str
    total_attempts: int
    failures: list[FailureRecord]
    root_cause: str
    root_cause_confirmed: bool
    strategies_tried: list[str]
    recommended_action: str
    
    def to_markdown(self) -> str: ...
    def save(self, change_dir: str, transport: Transport) -> None: ...
```

## Files to Create / Modify

| File | Action | Description |
|------|--------|-------------|
| `zsiga/agent/recovery.py` | **CREATE** | New module: `RecoveryManager`, `RecoveryAction`, `RecoveryReport` |
| `zsiga/pipeline/orchestrator.py` | **MODIFY** | Replace `EscalationManager` usage with `RecoveryManager` in `_run_phases`, `_fix_loop`, `_eval_fix_loop`, `_handle_escalation_abort` |
| `tests/test_recovery.py` | **CREATE** | Unit tests for `RecoveryManager` (failure tracking, rollback threshold, strategy rotation, report generation) |

## Key Design Decisions

1. **RecoveryManager wraps, not replaces, EscalationManager** — Internal composition, `EscalationManager` remains untouched and importable.

2. **RCA runs on every failure** — Even on first failure, we generate a root cause hypothesis. This is cheap (rule-based, no LLM) and provides context for strategy hints.

3. **Rollback threshold is configurable** — Default 3, overridable via constructor. The orchestrator can pass a different value from `PipelineConfig` if needed.

4. **Report uses `recovery-report.md`** — Distinct from the existing `escalation-{name}.md` and `diagnosis.md` to avoid conflicts during transition. The old files continue to exist for backward compatibility.

5. **Strategy hint is a plain string** — No structured prompt format; the orchestrator injects it into the fix system prompt as-is, matching the existing pattern in `_fix_loop`.

6. **Transport-aware** — All remote operations (git reset, file saves) go through `Transport`, consistent with the existing codebase pattern.
