# Tasks: Prompt Compaction Strategy

## Group 1: Token estimation and core infrastructure

- [x] **1.1** Add `estimate_tokens` function and helper `_count_tool_overhead`
  - Add `estimate_tokens(messages, overhead_per_message=15, overhead_per_tool_call=20)` that wraps `estimate_chars` with per-message and per-tool-call overhead
  - Add `_count_tool_overhead(msg)` helper that returns token overhead for a single message based on its role and tool_calls
  - Keep existing `estimate_chars` untouched for backward compat
  - File: `zsiga/agent/compaction.py`
  - Est: 2 rounds

## Group 2: Tool-call chain preservation

- [x] **2.1** Implement `_preserve_tool_chains` to replace current orphan-tool-id logic
  - Build a map of `tool_call_id → parent_assistant_msg_index` for all compressible messages
  - For each tool result in recent messages, look up the parent assistant message, then collect ALL tool_call_ids from that parent and find ALL corresponding tool results
  - Return `(preserved_assistant_indices, preserved_tool_result_indices)` sets
  - File: `zsiga/agent/compaction.py`
  - Est: 2 rounds

## Group 3: Pattern compression (Phase 1)

- [x] **3.1** Implement pattern compression layer (`_compress_patterns`, `_merge_tool_groups`, `_truncate_tool_result`)
  - `_truncate_tool_result(msg, max_chars)` — truncate content to `max_chars//2` + truncation marker if over limit
  - `_merge_tool_groups(messages)` — walk messages, identify consecutive tool-call rounds for the same tool, merge into consolidated entries with truncated results
  - `_compress_patterns(messages, max_tool_result_chars=2000)` — truncate long results, then merge groups, return compressed message list
  - File: `zsiga/agent/compaction.py`
  - Est: 3 rounds

## Group 4: Two-phase compaction rewrite

- [x] **4.1** Rewrite `compact_messages` to use two-phase flow
  - Phase 1: call `_compress_patterns` on the compressible section
  - Re-check threshold with `estimate_tokens`; if below threshold, skip Phase 2 and return pattern-compressed messages
  - Phase 2: call existing `_generate_summary` on the pattern-compressed compressible section
  - Use `_preserve_tool_chains` for chain preservation instead of old orphan-tool-id logic
  - Add optional keyword params `max_tool_result_chars`, `overhead_per_message`, `overhead_per_tool_call` with defaults
  - Maintain existing return type `tuple[list, int]`
  - File: `zsiga/agent/compaction.py`
  - Est: 2 rounds

## Group 5: Improved fallback summary

- [x] **5.1** Upgrade `_fallback_summary` with structured extraction
  - Extract: message count, tool-call count, unique files read (from `read_file` args), unique files written (from `write_file` args), unique shell commands (from `bash` args, deduplicated), error count
  - Format as structured bullet list
  - File: `zsiga/agent/compaction.py`
  - Est: 1 round

## Group 6: Loop integration and tests

- [x] **6.1** Update `AgentLoop.run` to use `estimate_tokens` and pass compaction config
  - Change import from `estimate_chars` to `estimate_tokens` in `loop.py`
  - Update the logging line in the compaction block to use `estimate_tokens`
  - Pass `max_tool_result_chars` from `CompactionConfig` if available (optional, with default fallback)
  - File: `zsiga/agent/loop.py`
  - Est: 1 round

- [x] **6.2** Add comprehensive tests for new compaction behavior
  - Test `estimate_tokens` (overhead counting, tool-call overhead)
  - Test `_preserve_tool_chains` (batched tool calls, no orphans, mixed)
  - Test `_compress_patterns` (merge consecutive same-tool calls, truncate long results, mixed tools not merged)
  - Test two-phase flow: Phase 1 alone sufficient, both phases needed, below threshold
  - Test improved `_fallback_summary` output format
  - Test backward compat: `compact_messages` with old signature still works
  - File: `tests/test_compaction.py`
  - Est: 3 rounds
