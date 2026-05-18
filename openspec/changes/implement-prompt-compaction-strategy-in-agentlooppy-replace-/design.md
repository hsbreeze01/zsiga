# Design: Prompt Compaction Strategy

## Architecture Decision

Replace the current single-phase compaction (compress → LLM summarize in one step) with a two-phase approach: **pattern compression** first, then **LLM summarization** if still over threshold. Add token-aware estimation that accounts for per-message and per-tool-call overhead.

### Why two phases?

The current approach sends all compressible messages directly to the LLM for summarization, even when many of those messages are repetitive (e.g., 20 `read_file` calls). This wastes LLM context tokens on redundant information. By compressing repeated patterns first, we reduce the summary input size and improve summary quality.

### Why token-aware estimation?

The current `estimate_chars` only counts content string length. In practice, each message carries 10-15 tokens of overhead (role, metadata), and tool-call messages carry additional 20+ tokens per tool call for the JSON schema. This leads to underestimation, causing compaction to trigger too late.

## Data Flow

```
AgentLoop.run (every 3 turns)
  │
  ├── estimate_tokens(messages)
  │     → counts content + per-message overhead + per-tool-call overhead
  │
  ├── if tokens > threshold:
  │     │
  │     ├── Phase 1: _compress_patterns(to_compress, max_tool_result_chars)
  │     │     │
  │     │     ├── Identify tool-call chains (assistant+tool pairs)
  │     │     ├── Merge consecutive same-tool calls into single entries
  │     │     ├── Truncate long tool results
  │     │     └── Return pattern-compressed messages
  │     │
  │     ├── Re-check: estimate_tokens(phase1_result) <= threshold?
  │     │     └── YES → return phase1_result (skip Phase 2)
  │     │
  │     └── Phase 2: _generate_summary(phase1_compressible, client, model)
  │           └── LLM summarizes the already-pattern-compressed section
  │
  └── Assemble: system + preserved_chains + summary + recent
```

## Tool-call chain preservation logic

Current: scans recent messages for orphan `tool_call_id`, walks backwards to find the matching assistant message.

New: for each tool result in recent messages, find its parent assistant message, then collect ALL tool results from that same assistant message (batch). This preserves complete round-trips.

## Pattern compression details

- **Grouping**: Walk compressible messages, group consecutive rounds where the same tool is called. A "round" = assistant message with tool_calls + corresponding tool result messages.
- **Merging**: For each group, produce a single assistant message with a consolidated content listing all arguments, and a single tool result with aggregated output.
- **Truncation**: Individual tool results > `max_tool_result_chars` are truncated to first half + marker.

## Files to modify

| File | Change |
|------|--------|
| `zsiga/agent/compaction.py` | Major rewrite: add `estimate_tokens`, `_compress_patterns`, `_merge_tool_groups`, `_truncate_tool_result`, `_preserve_tool_chains`; modify `compact_messages` to use two-phase flow; improve `_fallback_summary` |
| `zsiga/agent/loop.py` | Update import to use `estimate_tokens` instead of `estimate_chars`; pass new config params from `CompactionConfig` |
| `tests/test_compaction.py` | Add tests for new functions and scenarios |

### No changes needed

- `zsiga/config.py` — `CompactionConfig` already has the fields we need (`enabled`, `threshold_chars`, `keep_recent`, `use_llm_summary`). We add `max_tool_result_chars` default in compaction.py, not in config (it's an internal tuning param).
- `zsiga.yaml` — No new config keys required; existing `compaction` section works as-is.

## Backward compatibility

- `estimate_chars` is kept as-is (tests still use it). New `estimate_tokens` is added alongside.
- `compact_messages` signature is extended with keyword-only optional params, all with defaults.
- Return type unchanged: `tuple[list, int]`.
