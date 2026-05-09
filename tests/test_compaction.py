import pytest
from zsiga.agent.compaction import estimate_chars, compact_messages, _fallback_summary


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


def test_compact_threshold_exact_match():
    msgs = [
        {"role": "system", "content": "a" * 100},
        {"role": "user", "content": "b" * 100},
    ]
    result, compacted = compact_messages(msgs, threshold=200, keep_recent=3)
    assert compacted == 0
    assert result == msgs
