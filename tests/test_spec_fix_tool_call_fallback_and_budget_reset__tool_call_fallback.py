"""Tests for tool call fallback parser spec.

Generated from: specs/tool-call-fallback.md
Change: fix-tool-call-fallback-and-budget-reset

Covers testable scenarios:
- Parse XML invoke tag with single parameter
- Parse XML invoke tag with multiple parameters
- Parse inline JSON tool call
- Parse markdown code block with JSON tool call
- Content with no tool call patterns returns empty list
- Empty or None content returns empty list
- Tool call embedded in explanatory text is still extracted
"""
import json

from zsiga.agent.loop import _extract_tool_calls_from_content


class TestXMLInvokeSingleParameter:
    """Scenario: Parse XML invoke tag with single parameter."""

    def test_read_file_in_tool_call_layout_container(self):
        content = (
            "<tool_call_layout>"
            "<invoke name=\"read_file\">"
            "<parameter name=\"path\">specs/foo.md</parameter>"
            "</invoke>"
            "</tool_call_layout>"
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "read_file"
        assert args == {"path": "specs/foo.md"}

    def test_read_file_without_container(self):
        content = (
            '<invoke name="read_file">'
            '<parameter name="path">specs/foo.md</parameter>'
            "</invoke>"
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "read_file"
        assert args == {"path": "specs/foo.md"}


class TestXMLInvokeMultipleParameters:
    """Scenario: Parse XML invoke tag with multiple parameters."""

    def test_write_file_two_params(self):
        content = (
            '<invoke name="write_file">'
            "<parameter name=\"path\">a.py</parameter>"
            "<parameter name=\"content\">hello</parameter>"
            "</invoke>"
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "write_file"
        assert args == {"path": "a.py", "content": "hello"}

    def test_bash_with_three_params(self):
        content = (
            '<invoke name="bash">'
            "<parameter name=\"command\">echo hi</parameter>"
            "<parameter name=\"timeout\">30</parameter>"
            "<parameter name=\"cwd\">/tmp</parameter>"
            "</invoke>"
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "bash"
        assert args["command"] == "echo hi"
        assert args["timeout"] == "30"
        assert args["cwd"] == "/tmp"


class TestInlineJSONToolCall:
    """Scenario: Parse inline JSON tool call."""

    def test_standalone_json_object(self):
        tool_json = json.dumps(
            {"name": "read_file", "arguments": {"path": "specs/bar.md"}}
        )
        result = _extract_tool_calls_from_content(tool_json)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "read_file"
        assert args == {"path": "specs/bar.md"}

    def test_json_with_nested_arguments(self):
        tool_json = json.dumps(
            {
                "name": "edit_file",
                "arguments": {
                    "path": "main.py",
                    "old_text": "foo = 1",
                    "new_text": "foo = 2",
                },
            }
        )
        result = _extract_tool_calls_from_content(tool_json)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "edit_file"
        assert args["old_text"] == "foo = 1"
        assert args["new_text"] == "foo = 2"


class TestMarkdownCodeBlockJSON:
    """Scenario: Parse markdown code block with JSON tool call."""

    def test_json_code_block(self):
        tool_obj = {"name": "bash", "arguments": {"command": "ls"}}
        content = f"```json\n{json.dumps(tool_obj)}\n```"
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "bash"
        assert args == {"command": "ls"}

    def test_code_block_with_surrounding_text(self):
        tool_obj = {"name": "read_file", "arguments": {"path": "x.py"}}
        content = (
            "I will now read the file:\n\n"
            f"```json\n{json.dumps(tool_obj)}\n```\n\n"
            "Let me analyze the results."
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "read_file"
        assert args == {"path": "x.py"}


class TestNoToolCallPatterns:
    """Scenario: Content with no tool call patterns returns empty list."""

    def test_plain_text_returns_empty(self):
        result = _extract_tool_calls_from_content(
            "This is just a regular response with no tool calls."
        )
        assert result == []

    def test_empty_string_returns_empty(self):
        result = _extract_tool_calls_from_content("")
        assert result == []

    def test_none_returns_empty(self):
        result = _extract_tool_calls_from_content(None)
        assert result == []

    def test_html_like_tags_not_tool_call(self):
        """Plain HTML should not be mistaken for tool call XML."""
        result = _extract_tool_calls_from_content(
            "<div><p>Hello world</p></div>"
        )
        assert result == []

    def test_random_json_not_tool_call(self):
        """JSON without name+arguments fields should not be extracted."""
        result = _extract_tool_calls_from_content(
            json.dumps({"status": "ok", "count": 42})
        )
        assert result == []


class TestMixedContentWithToolCall:
    """Scenario: Tool call embedded in explanatory text is still extracted."""

    def test_json_embedded_in_text(self):
        tool_obj = {"name": "read_file", "arguments": {"path": "x.md"}}
        content = (
            "Let me read the spec file for you. "
            + json.dumps(tool_obj)
            + " That should give us the information we need."
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "read_file"
        assert args == {"path": "x.md"}

    def test_xml_invoke_embedded_in_text(self):
        content = (
            "Sure, I'll check that file now.\n"
            '<invoke name="read_file"><parameter name="path">README.md</parameter></invoke>\n'
            "Here's what I found."
        )
        result = _extract_tool_calls_from_content(content)
        assert len(result) >= 1
        name, args = result[0]
        assert name == "read_file"
        assert args == {"path": "README.md"}
