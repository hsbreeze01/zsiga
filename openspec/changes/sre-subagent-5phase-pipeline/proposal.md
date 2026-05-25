# sre-subagent-5phase-pipeline

## Summary
Upgrade the operator sub-agent from a single-shot execution model to a structured 5-phase SRE pipeline: Diagnose → Plan → Execute → Verify → Report.

## Problem
The current `_dispatch_operator` in `orchestrator.py` sends the entire proposal text to a single operator agent with no structure. This causes:
1. **No diagnostic rigor** — operator skips investigation and guesses the fix
2. **No verification** — operator says "done" without confirming the action succeeded
3. **No recovery** — if execution fails halfway, there is no retry or rollback
4. **No report** — no structured output for the pipeline to learn from

Real SRE tasks (restart service, check disk, sync repo, clean logs) need a disciplined sequence: understand the situation, decide what to do, do it, confirm it worked, document what happened.

## Technical Design
Modify `zsiga/pipeline/orchestrator.py`, specifically `_dispatch_operator`.

### Phase 1: Diagnose
- Read proposal text and extract the SRE task
- Gather system state: `systemctl status`, `df -h`, `free -m`, `ps aux`, relevant logs
- Produce a structured diagnosis summary

### Phase 2: Plan
- Based on diagnosis, produce a step-by-step execution plan
- Each step must be a single shell command or API call
- Plan must include a rollback command for destructive operations

### Phase 3: Execute
- Execute plan steps sequentially
- After each step, capture output and check for errors
- If a step fails, stop and report failure with partial output

### Phase 4: Verify
- Re-run diagnostic commands from Phase 1
- Compare before/after state
- Confirm the intended change was applied

### Phase 5: Report
- Generate structured report: diagnosis, plan, execution log, verification result
- Write to `change_dir/sre-report.md`
- Return success/failure to orchestrator

### Implementation Approach
Each phase is a separate `run_sub_agent` call with a specific system prompt. State (diagnosis, plan, execution log) is passed between phases via temp files in `change_dir/`. The orchestrator manages phase transitions and error handling.

Key files to modify:
- `zsiga/pipeline/orchestrator.py` — rewrite `_dispatch_operator` with 5-phase loop
- `zsiga/agent/roles.py` — add SRE-specific system prompts for each phase

## Acceptance Criteria
1. `_dispatch_operator` runs 5 phases sequentially (Diagnose → Plan → Execute → Verify → Report)
2. Each phase gets a dedicated system prompt targeting its specific responsibility
3. Diagnosis state is captured before execution and compared after
4. `sre-report.md` is written to `change_dir/` with structured output
5. Existing pipeline continues to work (no regression in non-SRE proposals)
6. If any phase fails, subsequent phases are skipped and report contains partial results

## Scope
- **In scope**: `_dispatch_operator` rewrite, SRE phase prompts, report generation
- **Out of scope**: New tools, new dependencies, changes to non-SRE intent routing

## Risk
- **Impact**: Medium — changes core SRE execution path
- **Blast radius**: Only affects proposals classified as SRE intent
- **Reversibility**: Revert `_dispatch_operator` to single-shot model
