# Design: Fix Review Role Write Permission

## Problem

The review sub-agent's role configuration (`Role.REVIEW` in `zsiga/agent/roles.py`) defines an `allowed_tools` list that omits `write_file`. However, `reviewer.py`'s prompt instructs the sub-agent to write its findings to `{change_dir}/review.md`. Since `run_sub_agent()` filters available tools through `_filter_tools_by_role()`, the sub-agent never receives `write_file` and cannot complete its task. This causes 100% review failures (verdict always `UNKNOWN`).

## Solution

Add `"write_file"` to the `Role.REVIEW` `allowed_tools` list in `zsiga/agent/roles.py`.

This is a single-line change: appending one string to an existing list.

### Why `write_file` and not `edit_file`

- Review only needs to **create** a new file (`review.md`), never modify existing implementation files.
- `edit_file` would grant the review sub-agent the ability to alter source code under review — a separation-of-concerns violation.
- `write_file` is sufficient and minimal for the review workflow.

### Why not change `reviewer.py`

- The prompt logic is correct; it correctly asks the sub-agent to write the review output.
- The bug is in the permission layer, not the instruction layer.

## Files Modified

| File | Change |
|------|--------|
| `zsiga/agent/roles.py` | Add `"write_file"` to `Role.REVIEW.allowed_tools` |

## Data Flow

```
run_review() → constructs prompt → run_sub_agent(role=REVIEW)
                                         ↓
                               _filter_tools_by_role(REVIEW)
                                         ↓
                               tools = agent_tools ∩ allowed_tools
                               (now includes write_file)
                                         ↓
                               sub-agent executes with write_file
                                         ↓
                               review.md written to change_dir
                                         ↓
                               parse_review_verdict() reads file → (CLEAN/ISSUES_FOUND, issues)
```

## Risk Assessment

- **Impact**: Minimal — only affects the review sub-agent's tool set.
- **Regression risk**: None expected; existing tests for `Role.REVIEW` should be updated to assert `write_file` presence.
- **No other roles affected**: EXPLORE, IMPLEMENT, DIAGNOSER configurations remain unchanged.
