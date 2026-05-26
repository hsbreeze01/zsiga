# fix-tool-call-fallback-and-budget-reset

## Summary
Fix two critical pipeline bugs: (1) LLM occasionally outputs XML-format tool calls instead of JSON, causing sub-agents to fail silently; (2) TokenBudget is never reset between phases, causing cascade failures after BUDGET_EXCEEDED.

## Problem

### Bug 1: XML Tool Call Not Executed
When glm-5.1 outputs tool calls in XML format (e.g. `<tool_call_layout><invoke name="read_file"><parameter name="path">...</parameter></invoke></tool_call_layout>`) instead of the standard OpenAI API `tool_calls` JSON field, the current code at `loop.py:223` sees `msg.tool_calls` as empty and returns the XML as final content.

Impact: Judge sub-agent outputs XML tool calls → tools not executed → Judge cannot read spec files → gives hallucinated FAIL verdict → Design Gate rejects valid specs → ENRICH retries with bad feedback → wastes 3+ ENRICH cycles.

### Bug 2: TokenBudget Never Resets
`AgentLoop` instance is shared across all phases of a proposal. `TokenBudget._used` accumulates across phases. When ENRICH exceeds budget (1.88M tokens used, budget=1.2M), all subsequent `agent.run()` calls immediately return `BUDGET_EXCEEDED` because the counter is already over limit.

Impact chain:
1. ENRICH hits BUDGET_EXCEEDED → specs partially written
2. Orchestrator records `Outcome.SUCCESS` (doesn't check result content)
3. Design Gate FAIL → triggers ENRICH retry
4. Retry ENRICH → AgentLoop.run() → first LLM call already over budget → immediate BUDGET_EXCEEDED return
5. Specs still incomplete → Design Gate FAIL again
6. This repeats until `design_gate_max_retries` exhausted → proposal SKIPPED
7. ~30 minutes wasted with zero productive work

## Technical Design

### Fix 1: Tool Call Fallback Parser
File: `zsiga/agent/loop.py`

Add `_extract_tool_calls_from_content(content: str) -> list[tuple[str, dict]]` function that detects and parses:
1. XML format: `<tool_call_layout><invoke name="X"><parameter name="Y">Z</parameter></invoke></tool_call_layout>`
2. Inline JSON: `{"name": "X", "arguments": {"Y": "Z"}}`
3. Markdown code block: `` ```json\n{"name": "X", ...} ``

Insert at line 223, before `return RunResult`:
```python
if not msg.tool_calls:
    # Fallback: try to extract tool calls from content
    extracted = _extract_tool_calls_from_content(msg.content or "")
    if extracted:
        # Convert to tool_calls-like objects and execute them
        # Then continue the turn loop instead of returning
        ...
    else:
        # No tool calls detected, this is a genuine final response
        return RunResult(msg.content, ...)
```

Security: only execute tools registered in `self.tool_funcs`. Log a warning when fallback parsing is triggered.

### Fix 2: Budget Reset Before Each Phase
File: `zsiga/pipeline/orchestrator.py`

Call `self.agent.budget = TokenBudget(...)` or `self.agent.reset_budget()` before each phase's `agent.run()` call. This ensures each phase starts with a fresh budget counter.

Specifically, add budget reset before:
- ENRICH: before line 689
- Design Gate ENRICH retry: before line 759
- IMPLEMENT: before line 897
- VERIFY: before line 1128

Also fix: check `result.content == "BUDGET_EXCEEDED"` in orchestrator after each phase. If detected, record `Outcome.FAIL` instead of `Outcome.SUCCESS`, and log a warning.

## Acceptance Criteria
1. When LLM outputs XML-format tool calls, the tools are still executed (log shows "fallback tool call parsed" warning)
2. When LLM outputs XML-format tool calls, the turn loop continues (doesn't return early)
3. Each phase starts with a fresh token budget (no carry-over from previous phases)
4. BUDGET_EXCEEDED is recorded as `Outcome.FAIL` in PhaseRecord, not `Outcome.SUCCESS`
5. After BUDGET_EXCEEDED, the pipeline logs a clear warning instead of silently continuing
6. Existing test suite passes (no regression in normal JSON tool call path)
7. Judge sub-agent with XML tool calls still produces valid verdict (PASS or FAIL based on actual specs)

## Scope
- **In scope**: `loop.py` fallback parser + orchestrator budget reset + outcome recording fix
- **Out of scope**: Changing LLM model, modifying tool definitions, changing budget thresholds

## Risk
- **Impact**: High — affects core LLM interaction loop
- **Blast radius**: All phases that use AgentLoop (enrich, implement, verify, review, judge)
- **Reversibility**: Single git revert. Both fixes are independent.
- **Mitigation**: Fallback parser only activates when `msg.tool_calls` is empty AND content contains tool-call patterns. Normal path is unchanged.
