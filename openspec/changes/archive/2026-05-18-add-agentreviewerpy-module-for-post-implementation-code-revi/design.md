# Design: agent/reviewer.py — Post-Implementation Code Review Loop

## Architecture Decision

Add a dedicated `reviewer.py` module in `zsiga/agent/` that encapsulates the review sub-agent dispatch and auto-fix loop logic. This follows the existing pattern where `pipeline/verifier.py` handles verification and `pipeline/diagnoser.py` handles diagnosis — the reviewer is a separate concern focused on spec-coverage and code-quality review before formal verification.

**Why a new module instead of extending verifier.py:** The reviewer uses the review-role sub-agent (read-only), while the verifier uses the main agent loop. They serve different purposes — reviewer checks spec completeness and code quality, verifier checks correctness against specs. Keeping them separate maintains single-responsibility and allows independent tuning.

## Data Flow

```
IMPLEMENT (mechanical verify passes)
    │
    ▼
REVIEW (new phase)
    │  ┌─────────────────────────────────────────┐
    │  │ 1. Create review-role sub-agent          │
    │  │ 2. Provide: specs + design + tasks + diff│
    │  │ 3. Sub-agent writes review.md             │
    │  │ 4. Parse verdict: CLEAN / ISSUES_FOUND   │
    │  │ 5. If ISSUES_FOUND + CRITICAL → auto-fix │
    │  │    a. Main agent fixes CRITICAL issues    │
    │  │    b. Re-run mechanical verify            │
    │  │    c. Re-dispatch review sub-agent        │
    │  │    d. Repeat up to review_max_rounds      │
    │  │ 6. Record PhaseRecord(REVIEW)             │
    │  └─────────────────────────────────────────┘
    │
    ▼
VERIFY (existing phase, unchanged)
```

## Key Design Decisions

1. **Use existing `Role.REVIEW` from `agent/roles.py`** — The review-role sub-agent already exists with read-only tools and an 8-turn budget. The reviewer module will use `create_with_role("review")` from `agent/sub_agent.py` to spawn review agents.

2. **Review writes `review.md`, not `verify.md`** — Separate artifacts so reviewer and verifier outputs don't conflict. `review.md` uses a different schema: `CLEAN/ISSUES_FOUND` instead of `PASS/FAIL`.

3. **Auto-fix uses the main agent loop** — The main `AgentLoop` has write tools. During auto-fix, the orchestrator reuses its main agent with a focused prompt derived from the review issues.

4. **Escalation integration** — The auto-fix loop uses the existing `EscalationManager` for consistent failure tracking across all fix loops.

5. **SUGGESTION-only reviews don't trigger fixes** — Only CRITICAL issues warrant the cost of an auto-fix cycle.

## Files to Create / Modify

### New Files
| File | Purpose |
|------|---------|
| `zsiga/agent/reviewer.py` | Core module: `run_review()`, `parse_review_verdict()`, auto-fix loop |
| `tests/test_reviewer.py` | Unit tests for reviewer module |

### Modified Files
| File | Change |
|------|--------|
| `zsiga/metrics/types.py` | Add `REVIEW = "review"` to Phase enum |
| `zsiga/pipeline/orchestrator.py` | Insert REVIEW phase between IMPLEMENT and VERIFY in `_run_phases` |
| `zsiga/config.py` | Add review config fields to `PipelineConfig` |

## Module Interface: `zsiga/agent/reviewer.py`

```python
async def run_review(
    agent: AgentLoop,
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport = None,
    max_turns: int = 10,
    timeout_seconds: int = 180,
) -> RunResult:
    """Dispatch review-role sub-agent to analyze implementation against specs.
    
    The sub-agent writes review.md in change_dir.
    Returns the RunResult from the sub-agent execution.
    """

def parse_review_verdict(change_dir: str, transport: Transport = None) -> tuple[str, list[dict]]:
    """Parse review.md and return (verdict, issues).
    
    verdict: "CLEAN" or "ISSUES_FOUND"
    issues: [{"severity": "CRITICAL"|"SUGGESTION", "description": str}, ...]
    """
```

## Integration Point: `orchestrator._run_phases`

The REVIEW phase is inserted after the mechanical verification block succeeds and before the existing VERIFY phase. The insertion point is around line ~350 in orchestrator.py (after the fix_loop block, before the Phase 3: VERIFY section).

Pseudo-code for the insertion:

```python
# After IMPLEMENT phase succeeds (mechanical verification passed)

# Phase 2.5: REVIEW
if not skip_enrich:  # Only for full pipeline, not for fix-only
    print(f"\n  {'='*50}")
    print(f"  Phase 2.5/5: REVIEW {change_name}")
    ...
    review_verdict, review_issues = await self._review_loop(...)
    rec.phases.append(PhaseRecord(phase=Phase.REVIEW, ...))

# Phase 3: VERIFY (existing, unchanged)
```

## Review Prompt Strategy

The review sub-agent receives:
- All specs from `change_dir/specs/` (via `_read_all_specs`)
- `design.md` content
- `tasks.md` content  
- Git diff since `pre_sha`
- Mechanical verification results (test + lint status)

The system prompt instructs it to:
1. Compare each spec requirement against the diff
2. Check for common code quality issues (dead code, missing error handling, naming)
3. Output structured `review.md` with verdict and categorized issues
