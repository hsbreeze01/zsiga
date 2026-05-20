# Design: Fix Recurring `pipeline.fail.implement` Pattern

## Problem Analysis

The `pipeline.fail.implement` pattern has occurred 6+ times with the following root causes:

| Error Code | Example | Count |
|-----------|---------|-------|
| E701 | `if not x: x = {}` on one line | 2 |
| E702 | `from dotenv import load_dotenv; load_dotenv()` | 1 |
| E401 | `import json, requests, datetime` | 2 |
| E741 | `l for l in lines` | 1 |
| Test failures | Assertion mismatches | 1 |

**Root cause**: The implementer's system prompt (`IMPLEMENTER_SYSTEM`) tells the agent NOT to run `ruff check`, but does NOT tell the agent which patterns to avoid. The LLM generates lint-violating code, then mechanical verification catches it, triggering fix loops that waste turns and sometimes fail entirely.

## Solution: Two-pronged prevention

### 1. Lint-prevention rules in IMPLEMENTER_SYSTEM

Add a `## Lint Prevention Rules` section to the `IMPLEMENTER_SYSTEM` constant in `implementer.py`. This section explicitly lists the top lint violations to avoid, with correct/incorrect examples. This is a static addition — no runtime logic needed.

**Why in system prompt?** The system prompt is always sent. Putting rules here guarantees every implementation turn sees them, unlike context that can be compacted away.

### 2. Pattern warnings injected into implementer user prompt

In `implementer.py`, the `implement()` function currently builds a user prompt from specs/design/tasks. We extend it to:
1. Call `pattern_miner.mine_patterns()` to get active patterns
2. Filter to high-severity patterns related to `pipeline.fail.*`
3. Format the top-3 as a "## Known Failure Patterns (AVOID)" section
4. Append to the user prompt

This ensures the agent sees the *specific* failure modes that have been recurring, not just generic rules.

## Data Flow

```
learnings.jsonl
    ↓ (pattern_miner.mine_patterns)
List[Pattern]  →  filter high-severity  →  top-3 warnings
    ↓
implement() builds user_prompt with warnings appended
    ↓
AgentLoop.run(system=IMPLEMENTER_SYSTEM + lint rules, user=prompt + warnings)
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/pipeline/implementer.py` | 1) Add lint-prevention section to `IMPLEMENTER_SYSTEM`. 2) Import `pattern_miner` and inject warnings into user prompt in `implement()`. |
| `tests/test_pattern_miner.py` | No change needed (pattern_miner already tested). |
| `tests/test_harness_runner.py` | May need update if harness tests cover implementer prompt construction. |

## Why this approach

- **Prevention > detection**: Adding rules to the system prompt prevents violations before they occur, reducing fix-loop consumption by ~30-50%.
- **Leverages existing infrastructure**: `pattern_miner` already mines patterns; we just surface them where they matter.
- **Zero new config**: No new config keys, no new files, no schema changes.
- **Backward compatible**: If pattern_miner returns empty, implementer works exactly as before.
