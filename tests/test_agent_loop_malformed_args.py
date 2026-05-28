from __future__ import annotations

from zsiga.agent.loop import _fallback_args_for_malformed_tool


def test_malformed_tool_args_fallback_allows_optional_args_tool() -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": [],
                },
            },
        }
    ]

    assert _fallback_args_for_malformed_tool("list_files", tools) == {}


def test_malformed_tool_args_fallback_refuses_required_args_tool() -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        }
    ]

    assert _fallback_args_for_malformed_tool("read_file", tools) is None


def test_malformed_tool_args_fallback_refuses_unknown_tool() -> None:
    assert _fallback_args_for_malformed_tool("missing", []) is None
