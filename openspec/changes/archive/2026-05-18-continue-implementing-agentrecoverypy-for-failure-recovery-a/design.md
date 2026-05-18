# Design: Implement agent/recovery.py — Failure Recovery Module

## Architecture Decision

Create `zsiga/agent/recovery.py` as a **composition layer** over the existing `EscalationManager` and `Diagnoser`. The `RecoveryManager` class owns the full recovery lifecycle:

1. **Failure tracking** → delegates to internal `EscalationManager`
2. **Root cause analysis** → delegates to internal `Diagnoser`
3. **Strategy rotation** → reads from `EscalationManager.next_strategy`
4. **Rollback decision + execution** → new logic wrapping `git_ops.reset_hard`
5. **Diagnostic report** → new `RecoveryReport` dataclass with markdown rendering

**Why composition over modification?** `EscalationManager` is a pure escalation tracker with its own persist logic. `Diagnoser` is a rule-based hypothesis engine. `RecoveryManager` orchestrates both at a higher level, adding git rollback and structured reporting. This preserves backward compatibility — `EscalationManager` and `Diagnoser` remain independently usable.

## Data Flow

```
ZsigaOrchestrator._run_phases()
  │
  ├── Creates RecoveryManager(change_name, target_path, pre_sha, transport, persist_dir, max_failures)
  │
  ├── Passes recovery to _fix_loop() / _eval_fix_loop()
  │
  │   fix loop iteration:
  │     failure occurs
  │       │
  │       ▼
  │     recovery.record_failure(error, phase)
  │       │
  │       ├── internal EscalationManager.record_failure() → track attempt
  │       │
  │       ├── internal Diagnoser.diagnose() → DiagnosisReport (RCA)
  │       │   (only if target_path + transport available)
  │       │
  │       └── returns RecoveryAction { strategy, strategy_hint, should_rollback, attempt, rca_report }
  │
  │   if RecoveryAction.should_rollback:
  │       │
  │       ▼
  │     recovery.execute_rollback()
  │       ├── git_ops.reset_hard(target_path, pre_sha, transport)
  │       ├── record_lesson(pattern_key="pipeline.fail.rollback")
  │       └── returns True
  │
  ├── if all strategies exhausted:
  │       │
  │       ▼
  │     recovery.generate_diagnostic_report()
  │       ├── compose RecoveryReport from failures + RCA
  │       ├── save to {change_dir}/recovery-report.md
  │       └── record_lesson(pattern_key="pipeline.fail.recovery")
  │
  └── else: inject RecoveryAction.strategy_hint into next fix attempt system prompt
```

## New Types

```python
# In zsiga/agent/recovery.py

@dataclass
class RecoveryAction:
    """Returned by record_failure() — tells orchestrator what to do next."""
    strategy: Strategy               # SAME / DIFFERENT_APPROACH / SIMPLIFY
    strategy_hint: str               # prompt modifier for fix engine
    should_rollback: bool            # whether to git reset --hard
    attempt: int                     # current attempt number
    rca_report: DiagnosisReport | None  # from pipeline.diagnoser

@dataclass
class RecoveryReport:
    """Full diagnostic report written on strategy exhaustion."""
    change_name: str
    total_attempts: int
    failures: list[FailureRecord]    # from escalation.py
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
| `zsiga/agent/recovery.py` | **CREATE** | `RecoveryManager`, `RecoveryAction`, `RecoveryReport` |
| `zsiga/pipeline/orchestrator.py` | **MODIFY** | Replace `EscalationManager` construction with `RecoveryManager`; update `_fix_loop`, `_eval_fix_loop`, `_handle_escalation_abort` to use `RecoveryAction` |
| `tests/test_recovery.py` | **CREATE** | Unit tests for failure tracking, rollback, strategy rotation, report generation |

## Key Design Decisions

1. **RecoveryManager wraps EscalationManager by composition** — Stores an internal `EscalationManager` instance. All failure tracking calls are forwarded. This means `EscalationManager` remains untouched and importable.

2. **RCA runs only when target_path + transport are available** — The `Diagnoser` requires shell access to probe the codebase. If we're in a unit test or context where transport is None, we skip RCA and set `rca_report=None`. This avoids forcing callers to always provide transport.

3. **Rollback threshold = max_failures constructor arg** — Default 3, matching the existing `_MAX_ATTEMPTS` in `escalation.py`. The orchestrator can override via `PipelineConfig` if needed.

4. **Strategy hints match existing orchestrator pattern** — The `DIFFERENT_APPROACH` and `SIMPLIFY` hint strings are copied verbatim from the current `_fix_loop` inline strings, ensuring no behavioral change during integration.

5. **RecoveryReport writes to `recovery-report.md`** — Distinct from `escalation-{name}.md` (from EscalationManager) and `diagnosis.md` (from Diagnoser). No conflicts during transition.

6. **Transport-aware saves** — `RecoveryReport.save()` uses the same `cat << 'EOF'` heredoc pattern as `Diagnoser.save()`, ensuring consistency with the codebase.

7. **Orchestrator passes `recovery` kwarg to _fix_loop and _eval_fix_loop** — Minimal API change: both methods already accept `escalation: EscalationManager`. We add `recovery: RecoveryManager = None` and prefer it when present, falling back to `escalation` for backward compat.
