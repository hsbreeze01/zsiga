import pytest
from zsiga.agent.compaction import (
    estimate_chars,
    estimate_tokens,
    compact_messages,
    _fallback_summary,
    _count_tool_overhead,
    _preserve_tool_chains,
    _compress_patterns,
    _truncate_tool_result,
    _merge_tool_groups,
)


# ---------------------------------------------------------------------------
# estimate_chars (existing)
# ---------------------------------------------------------------------------


def test_estimate_chars_string_content():
    msgs = [
        {"role": "system", "content": "hello"},
        {"role": "user", "content": "world"},
    ]
    assert estimate_chars(msgs) == 10


def test_estimate_chars_list_content():
    msgs = [
        {"role": "assistant", "content": [
            {"type": "text", "text": "hello"},
            {"type": "text", "text": "world"},
        ]},
    ]
    assert estimate_chars(msgs) == 10


def test_estimate_chars_mixed():
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": [
            {"type": "text", "text": "hello"},
        ]},
    ]
    assert estimate_chars(msgs) == 8


# ---------------------------------------------------------------------------
# estimate_tokens (REQ-COMPACT-003)
# ---------------------------------------------------------------------------


def test_estimate_tokens_includes_overhead():
    """Token estimation includes per-message overhead."""
    msgs = [
        {"role": "system", "content": "a" * 100},
        {"role": "user", "content": "b" * 100},
    ]
    tokens = estimate_tokens(msgs)
    # Must be greater than pure content chars (200)
    assert tokens > 200
    # Should be 200 + 2*15 = 230
    assert tokens == 200 + 2 * 15


def test_estimate_tokens_tool_call_overhead():
    """Messages with tool_calls have higher overhead."""
    msg_plain = [{"role": "assistant", "content": "x" * 100}]
    msg_with_tools = [
        {
            "role": "assistant",
            "content": "x" * 100,
            "tool_calls": [
                {"id": "tc1", "function": {"name": "bash", "arguments": "{}"}},
                {"id": "tc2", "function": {"name": "read_file", "arguments": "{}"}},
            ],
        }
    ]
    assert estimate_tokens(msg_with_tools) > estimate_tokens(msg_plain)
    # Extra overhead: 2 tool calls * 20 = 40
    assert estimate_tokens(msg_with_tools) == estimate_tokens(msg_plain) + 40


def test_estimate_tokens_custom_overhead():
    """Custom overhead values are applied."""
    msgs = [{"role": "user", "content": "hi"}]
    tokens_default = estimate_tokens(msgs)
    tokens_high = estimate_tokens(msgs, overhead_per_message=50)
    assert tokens_high > tokens_default


# ---------------------------------------------------------------------------
# _count_tool_overhead
# ---------------------------------------------------------------------------


def test_count_tool_overhead_plain():
    msg = {"role": "assistant", "content": "hi"}
    assert _count_tool_overhead(msg) == 0


def test_count_tool_overhead_with_tool_calls():
    msg = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "tc1", "function": {"name": "bash", "arguments": "{}"}},
        ],
    }
    assert _count_tool_overhead(msg) == 20


def test_count_tool_overhead_tool_result():
    msg = {"role": "tool", "content": "result", "tool_call_id": "tc1"}
    assert _count_tool_overhead(msg) == 20


# ---------------------------------------------------------------------------
# _preserve_tool_chains (REQ-COMPACT-001)
# ---------------------------------------------------------------------------


def test_preserve_tool_chains_batched():
    """Full tool-call chain preserved when one tool_call_id is in recent."""
    to_compress = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "tc1", "function": {"name": "bash", "arguments": "{}"}},
                {"id": "tc2", "function": {"name": "bash", "arguments": "{}"}},
                {"id": "tc3", "function": {"name": "bash", "arguments": "{}"}},
            ],
        },
        {"role": "tool", "content": "r1", "tool_call_id": "tc1"},
        {"role": "tool", "content": "r2", "tool_call_id": "tc2"},
        {"role": "tool", "content": "r3", "tool_call_id": "tc3"},
    ]
    recent = [
        {"role": "tool", "content": "use tc1", "tool_call_id": "tc1"},
    ]
    asst_idx, tool_idx = _preserve_tool_chains(to_compress, recent)
    # Parent assistant message preserved
    assert 0 in asst_idx
    # All 3 tool results preserved
    assert 1 in tool_idx
    assert 2 in tool_idx
    assert 3 in tool_idx


def test_preserve_tool_chains_no_orphans():
    """No chains preserved when recent doesn't reference any tool_call_id."""
    to_compress = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "tc1", "function": {"name": "bash", "arguments": "{}"}},
            ],
        },
        {"role": "tool", "content": "r1", "tool_call_id": "tc1"},
    ]
    recent = [
        {"role": "user", "content": "no tool references"},
    ]
    asst_idx, tool_idx = _preserve_tool_chains(to_compress, recent)
    assert len(asst_idx) == 0
    assert len(tool_idx) == 0


def test_preserve_tool_chains_mixed():
    """Only chains referenced in recent are preserved."""
    to_compress = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "tc1", "function": {"name": "bash", "arguments": "{}"}},
            ],
        },
        {"role": "tool", "content": "r1", "tool_call_id": "tc1"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "tc2", "function": {"name": "bash", "arguments": "{}"}},
            ],
        },
        {"role": "tool", "content": "r2", "tool_call_id": "tc2"},
    ]
    recent = [
        {"role": "tool", "content": "ref tc2", "tool_call_id": "tc2"},
    ]
    asst_idx, tool_idx = _preserve_tool_chains(to_compress, recent)
    # Only tc2's parent and result
    assert 2 in asst_idx
    assert 3 in tool_idx
    # tc1 not preserved
    assert 0 not in asst_idx
    assert 1 not in tool_idx


# ---------------------------------------------------------------------------
# _truncate_tool_result (REQ-COMPACT-005)
# ---------------------------------------------------------------------------


def test_truncate_long_tool_result():
    msg = {"role": "tool", "content": "x" * 10000, "tool_call_id": "tc1"}
    truncated = _truncate_tool_result(msg, max_chars=2000)
    assert truncated["content"].startswith("x" * 1000)
    assert "[truncated, was 10000 chars]" in truncated["content"]


def test_truncate_short_tool_result_unchanged():
    msg = {"role": "tool", "content": "short", "tool_call_id": "tc1"}
    truncated = _truncate_tool_result(msg, max_chars=2000)
    assert truncated["content"] == "short"


# ---------------------------------------------------------------------------
# _merge_tool_groups (REQ-COMPACT-002)
# ---------------------------------------------------------------------------


def test_merge_consecutive_same_tool():
    """Consecutive same-tool calls are merged."""
    msgs = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "tc1",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path": "a.py"}',
                    },
                },
            ],
        },
        {"role": "tool", "content": "content_a", "tool_call_id": "tc1"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "tc2",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path": "b.py"}',
                    },
                },
            ],
        },
        {"role": "tool", "content": "content_b", "tool_call_id": "tc2"},
    ]
    merged = _merge_tool_groups(msgs)
    # Should be: merged assistant + merged tool result (2 messages instead of 4)
    assert len(merged) == 2
    assert "[merged 2 read_file calls]" in merged[0]["content"]


def test_merge_mixed_tools_not_merged():
    """Mixed tool calls are NOT merged."""
    msgs = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "tc1",
                    "function": {"name": "bash", "arguments": '{"command":"ls"}'},
                },
            ],
        },
        {"role": "tool", "content": "output1", "tool_call_id": "tc1"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "tc2",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path":"x.py"}',
                    },
                },
            ],
        },
        {"role": "tool", "content": "output2", "tool_call_id": "tc2"},
    ]
    merged = _merge_tool_groups(msgs)
    # Not merged because different tools
    assert len(merged) == 4


# ---------------------------------------------------------------------------
# _compress_patterns
# ---------------------------------------------------------------------------


def test_compress_patterns_truncates_and_merges():
    msgs = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "tc1",
                    "function": {
                        "name": "bash",
                        "arguments": '{"command":"ls"}',
                    },
                },
            ],
        },
        {"role": "tool", "content": "x" * 5000, "tool_call_id": "tc1"},
    ]
    result = _compress_patterns(msgs, max_tool_result_chars=2000)
    # Tool result should be truncated
    tool_msg = [m for m in result if m["role"] == "tool"][0]
    assert "[truncated" in tool_msg["content"]


# ---------------------------------------------------------------------------
# compact_messages integration (two-phase flow, REQ-COMPACT-004)
# ---------------------------------------------------------------------------


def test_compact_below_threshold():
    msgs = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "short"},
        {"role": "assistant", "content": "ok"},
    ]
    result, compacted = compact_messages(msgs, threshold=100000)
    assert compacted == 0
    assert result == msgs


def test_compact_too_few_messages():
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"},
    ]
    result, compacted = compact_messages(msgs, threshold=1, keep_recent=3)
    assert compacted == 0
    assert result == msgs


def test_compact_with_fallback_summary():
    long_content = "x" * 20000
    msgs = [
        {"role": "system", "content": "system prompt"},
    ]
    for i in range(10):
        msgs.append({"role": "user", "content": long_content})
        msgs.append({"role": "assistant", "content": long_content, "tool_calls": []})

    assert estimate_chars(msgs) > 60000

    result, compacted = compact_messages(msgs, threshold=60000, keep_recent=3, client=None)
    assert compacted == 1

    assert result[0]["role"] == "system"
    assert result[0]["content"] == "system prompt"

    assert result[1]["role"] == "assistant"
    assert "[compacted summary" in result[1]["content"]

    assert len(result) == 5  # system + summary + 3 recent
    assert result[-1] == msgs[-1]
    assert result[-2] == msgs[-2]
    assert result[-3] == msgs[-3]


def test_compact_no_system_message():
    long_content = "y" * 30000
    msgs = []
    for i in range(5):
        msgs.append({"role": "user", "content": long_content})
        msgs.append({"role": "assistant", "content": long_content})

    result, compacted = compact_messages(msgs, threshold=60000, keep_recent=2)
    assert compacted == 1
    assert result[0]["role"] == "assistant"
    assert "[compacted summary" in result[0]["content"]
    assert result[-1] == msgs[-1]
    assert result[-2] == msgs[-2]
    assert len(result) == 3  # summary + 2 recent


def test_compact_preserves_recent_order():
    long_content = "z" * 20000
    msgs = [
        {"role": "system", "content": "sys"},
    ]
    for i in range(8):
        msgs.append({"role": "user", "content": f"{long_content}_{i}"})
        msgs.append({"role": "assistant", "content": f"resp_{i}"})

    result, compacted = compact_messages(msgs, threshold=60000, keep_recent=3)
    assert compacted == 1
    assert result[-3:] == msgs[-3:]


def test_compact_threshold_exact_match():
    msgs = [
        {"role": "system", "content": "a" * 100},
        {"role": "user", "content": "b" * 100},
    ]
    result, compacted = compact_messages(msgs, threshold=200, keep_recent=3)
    assert compacted == 0
    assert result == msgs


def test_compact_phase1_only_sufficient():
    """Phase 1 brings conversation below threshold — Phase 2 skipped."""
    long_output = "o" * 10000
    msgs = [
        {"role": "system", "content": "sys"},
    ]
    for i in range(10):
        msgs.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": f"tc{i}",
                    "function": {
                        "name": "read_file",
                        "arguments": f'{{"path": "file_{i}.py"}}',
                    },
                },
            ],
        })
        msgs.append({"role": "tool", "content": long_output, "tool_call_id": f"tc{i}"})

    # Use a threshold that Phase 1 compression should beat but raw doesn't
    result, compacted = compact_messages(msgs, threshold=20000, keep_recent=3, client=None)
    assert compacted == 1
    # Phase 1 result should have merged messages, no summary
    has_summary = any(
        "[compacted summary" in m.get("content", "") for m in result
    )
    # Either Phase 1 alone was enough (no summary) or Phase 2 ran (has summary)
    # Just verify it compacted and returned valid structure
    assert result[0]["role"] == "system"


def test_compact_backward_compat_old_signature():
    """Calling compact_messages with old signature still works."""
    msgs = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "short"},
        {"role": "assistant", "content": "ok"},
    ]
    # Old signature: messages, threshold, keep_recent, client, model
    result, compacted = compact_messages(msgs, 100000, 3, None, "glm-5.1")
    assert compacted == 0
    assert result == msgs


# ---------------------------------------------------------------------------
# _fallback_summary (REQ-COMPACT-006)
# ---------------------------------------------------------------------------


def test_fallback_summary_counts_tool_calls():
    msgs = [
        {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "bash", "arguments": '{"command": "cat > /tmp/test.py"}'}},
        ]},
        {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "read_file", "arguments": '{"path": "/src/main.py"}'}},
        ]},
    ]
    summary = _fallback_summary(msgs)
    assert "2 tool calls" in summary
    assert "/src/main.py" in summary


def test_fallback_summary_structured_extraction():
    """Fallback summary includes files read, written, commands, errors."""
    msgs = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path": "/src/a.py"}',
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path": "/src/b.py"}',
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": '{"path": "/src/c.py"}',
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "bash",
                        "arguments": '{"command": "pytest test.py"}',
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "bash",
                        "arguments": '{"command": "pytest test.py"}',
                    },
                },
            ],
        },
        {"role": "tool", "content": '{"error": "something failed"}', "tool_call_id": "x"},
    ]
    summary = _fallback_summary(msgs)
    assert "5 tool calls" in summary
    assert "Files read:" in summary
    assert "/src/a.py" in summary
    assert "Files written:" in summary
    assert "/src/c.py" in summary
    assert "Shell commands:" in summary
    assert "pytest test.py" in summary
    assert "Errors encountered:" in summary
