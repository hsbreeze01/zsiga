# Spec: Prompt Compaction Strategy

## MODIFIED Requirements

### REQ-COMPACT-001: Intelligent tool-call result preservation

The compaction algorithm SHALL preserve complete tool-call chains (assistant message with `tool_calls` + all corresponding `role=tool` response messages) when the tool results are referenced by messages in the `keep_recent` window.

Previously, only assistant messages whose `tool_call_id` matched an orphan tool result in the recent window were preserved. The new behavior SHALL preserve the full round-trip: the assistant's tool-call message AND all its corresponding tool result messages, even if some tool results from that batch are not directly referenced in recent messages.

#### Scenario: Full tool-call chain preserved for batched tool calls
- Given a conversation with an assistant message containing 3 tool calls (ids `tc1`, `tc2`, `tc3`) and 3 corresponding tool result messages
- And one of the recent messages references `tc1` via `tool_call_id`
- When compaction runs
- Then the assistant message containing all 3 tool calls SHALL be preserved
- And ALL 3 tool result messages (for `tc1`, `tc2`, `tc3`) SHALL be preserved
- And the summary SHALL only cover messages that are not preserved

#### Scenario: No orphan references — no tool-call chain preserved
- Given a conversation with tool-call chains in the middle section
- And no recent messages reference any `tool_call_id` from those chains
- When compaction runs
- Then those tool-call chains SHALL be included in the summary, not preserved individually

### REQ-COMPACT-002: Repeated pattern compression

The compaction algorithm SHALL detect and compress repeated tool-call patterns before generating summaries. When the same tool is called multiple times with similar arguments (e.g., repeated `read_file` calls, repeated `bash` commands), the algorithm SHALL merge consecutive calls of the same tool into a single compact representation listing the arguments, rather than including each call's full output in the summary input.

#### Scenario: Consecutive read_file calls compressed
- Given 5 consecutive `read_file` tool-call rounds for `a.py`, `b.py`, `c.py`, `d.py`, `e.py`
- When compaction runs and these messages are in the compressible section
- Then the summary input SHALL contain a single entry like "read_file: a.py, b.py, c.py, d.py, e.py" instead of 5 separate rounds
- And the compressed representation SHALL preserve the file paths but truncate individual file contents

#### Scenario: Mixed tool calls not falsely merged
- Given consecutive tool calls: `bash`, `read_file`, `bash`, `write_file`
- When compaction runs
- Then only the two `bash` calls SHALL be candidates for merging
- And `read_file` and `write_file` SHALL remain separate entries

### REQ-COMPACT-003: Token-aware estimation with tool-call overhead

The `estimate_chars` function SHALL be replaced by a `estimate_tokens` function that provides a more accurate token count approximation. The estimation SHALL account for:
- Message overhead per message (role metadata, formatting tokens)
- Tool-call schema overhead (function name, arguments JSON structure, `tool_call_id` fields)
- Content length with a character-to-token ratio

#### Scenario: Token estimation includes message overhead
- Given a conversation with 10 messages each containing 100 characters of content
- When `estimate_tokens` is called
- Then the result SHALL be greater than `10 * 100` (pure content chars)
- And the overhead SHALL account for approximately 10-15 tokens per message for role/metadata

#### Scenario: Tool-call messages have higher overhead
- Given a message with `role=assistant` containing 2 tool calls
- When `estimate_tokens` is called
- Then the overhead for this message SHALL be higher than a plain assistant message with the same content length
- And the overhead SHALL account for tool-call schema structure (~20 tokens per tool call)

### REQ-COMPACT-004: Two-phase compaction (compress patterns → summarize)

The compaction algorithm SHALL operate in two phases:
1. **Phase 1 — Pattern compression**: Merge repeated tool-call patterns in the compressible section, reducing the raw message volume
2. **Phase 2 — LLM summarization**: Generate an LLM summary of the pattern-compressed section

If the char/token count after Phase 1 is already below the threshold, Phase 2 SHALL be skipped.

#### Scenario: Phase 1 alone brings conversation below threshold
- Given a conversation of 80,000 chars where repeated patterns account for 40,000 chars
- And the threshold is 60,000 chars
- When compaction runs
- Then Phase 1 SHALL compress repeated patterns
- And after Phase 1 the conversation SHALL be below 60,000 chars
- And Phase 2 (LLM summary) SHALL be skipped
- And the function SHALL return the pattern-compressed messages with `compacted=1`

#### Scenario: Both phases needed
- Given a conversation of 120,000 chars
- And the threshold is 60,000 chars
- When compaction runs
- Then Phase 1 SHALL compress repeated patterns first
- Then Phase 2 SHALL summarize the remaining compressible messages
- And the result SHALL contain: system + preserved chains + summary + recent messages

### REQ-COMPACT-005: Tool-result content truncation in pattern compression

During Phase 1 pattern compression, individual tool result contents that exceed a configurable `max_tool_result_chars` (default: 2000) SHALL be truncated to the first `max_tool_result_chars // 2` characters plus a truncation marker. This applies only to messages in the compressible section, not to preserved or recent messages.

#### Scenario: Long tool result truncated during pattern compression
- Given a tool result message with 10,000 characters of content in the compressible section
- And `max_tool_result_chars` is 2000
- When Phase 1 pattern compression runs
- Then the tool result content SHALL be truncated to 1000 chars + `"... [truncated, was 10000 chars]"`

#### Scenario: Short tool result preserved as-is
- Given a tool result message with 500 characters of content in the compressible section
- And `max_tool_result_chars` is 2000
- When Phase 1 pattern compression runs
- Then the tool result content SHALL remain unchanged

### REQ-COMPACT-006: Improved fallback summary with structured extraction

The `_fallback_summary` function SHALL produce a structured summary containing:
- Total message count and tool-call count
- Unique files read and files written (extracted from tool-call arguments)
- Unique shell commands executed (deduplicated)
- Error occurrences count

#### Scenario: Fallback summary includes structured information
- Given messages with 3 `read_file` calls, 2 `write_file` calls, 4 `bash` calls (2 unique), and 1 error result
- When `_fallback_summary` runs
- Then the summary SHALL contain the message/tool-call counts
- And SHALL list the unique file paths
- And SHALL list unique commands
- And SHALL mention the error occurrence

### REQ-COMPACT-007: Backward-compatible API

The `compact_messages` function SHALL maintain its existing signature and return type. New parameters (`max_tool_result_chars`, `overhead_per_message`, `overhead_per_tool_call`) SHALL have sensible defaults so that existing callers (including `AgentLoop.run`) continue to work without changes.

#### Scenario: Existing call site unchanged
- Given `AgentLoop.run` calls `compact_messages(messages, threshold=self.compaction_threshold, keep_recent=self.compaction_keep_recent, client=self.client, model=self.model)`
- When the upgraded `compact_messages` is called with these arguments
- Then it SHALL work correctly using default values for new parameters
- And the return type SHALL remain `tuple[list, int]`
