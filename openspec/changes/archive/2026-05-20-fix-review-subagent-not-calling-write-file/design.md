# Design: Fix Review Sub-Agent Not Calling write_file

## Problem

The review sub-agent has `write_file` in its `allowed_tools` but the LLM chooses to output review content as plain text in its reply instead of calling the tool. This means `review.md` is never created on disk, and `parse_review_verdict` always returns UNKNOWN.

## Architecture Decision

**Two-layer fix: prompt hardening + defensive fallback.**

1. **Prompt hardening (primary)**: Rewrite the user prompt in `run_review()` to make the `write_file` tool call a non-negotiable, explicit instruction rather than a soft suggestion. Use imperative language ("You MUST call write_file...") and place the instruction prominently.

2. **Defensive fallback (secondary)**: After the sub-agent returns, check if `review.md` was actually created. If not, and the content contains a `Verdict:` line, write it ourselves. This handles the case where the LLM still ignores the prompt instruction.

## Data Flow

```
run_review(change_dir, ...)
  │
  ├─ Build user_prompt with explicit write_file instruction
  │
  ├─ Call sub_agent.run(prompt)
  │     → SubAgentResult(content="...Verdict: CLEAN...")
  │
  ├─ Check: does {change_dir}/review.md exist?
  │     ├─ YES → proceed (sub-agent did its job)
  │     └─ NO  + content has "Verdict:" → write content to file (fallback)
  │              + no "Verdict:" → skip (nothing to persist)
  │
  └─ Return SubAgentResult (unchanged)
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/agent/reviewer.py` | 1. Modify `run_review()` user_prompt to include explicit write_file instruction. 2. Add post-run fallback check that writes content to `{change_dir}/review.md` if file is missing but content contains Verdict. |

## Files NOT Modified

- `zsiga/agent/roles.py` — `allowed_tools` is already correct
- `zsiga/agent/reviewer.py` `parse_review_verdict` — logic unchanged
- Any metrics or logging code
