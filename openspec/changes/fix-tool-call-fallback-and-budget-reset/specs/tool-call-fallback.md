# Tool Call Fallback Parser

## ADDED Requirements

### Requirement: Fallback Tool Call Extraction from Content

When `msg.tool_calls` is empty or None, the system SHALL invoke `_extract_tool_calls_from_content(msg.content)` to attempt parsing tool calls from the raw text content. The function SHALL handle three non-standard LLM output formats:

1. **XML `<invoke>` tags** — `<invoke name="X"><parameter name="Y">Z</parameter>...</invoke>` wrapped in any container tags
2. **Inline JSON objects** — standalone `{"name": "X", "arguments": {"Y": "Z"}}`
3. **Markdown code blocks** — fenced ` ```json ``` ` blocks containing JSON tool call objects

The function SHALL return a list of `(tool_name, arguments_dict)` tuples. When no patterns are detected, it SHALL return an empty list.

#### Scenario: Parse XML invoke tag with single parameter

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content contains `<invoke name="read_file"><parameter name="path">specs/foo.md</parameter></invoke>` wrapped in any XML container tags
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL return a list containing at least one tuple whose first element is `"read_file"` and second element is `{"path": "specs/foo.md"}`

#### Scenario: Parse XML invoke tag with multiple parameters

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content contains `<invoke name="write_file"><parameter name="path">a.py</parameter><parameter name="content">hello</parameter></invoke>`
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL return a list containing at least one tuple where the tool name is `"write_file"` and arguments include both `"path": "a.py"` and `"content": "hello"`

#### Scenario: Parse inline JSON tool call

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content is a standalone JSON object `{"name": "read_file", "arguments": {"path": "specs/bar.md"}}`
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL return a list containing at least one tuple with tool name `"read_file"` and arguments `{"path": "specs/bar.md"}`

#### Scenario: Parse markdown code block with JSON tool call

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content contains a fenced code block ` ```json ... ``` ` with `{"name": "bash", "arguments": {"command": "ls"}}`
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL return a list containing at least one tuple with tool name `"bash"` and arguments `{"command": "ls"}`

#### Scenario: Content with no tool call patterns returns empty list

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content is plain text with no `<invoke>` tags, no JSON objects containing `name` + `arguments`, and no code blocks with tool JSON
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL return an empty list `[]`

#### Scenario: Empty or None content returns empty list

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content is an empty string or None
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL return an empty list `[]` without raising an exception

#### Scenario: Tool call embedded in explanatory text is still extracted

- **testable**: true
- **target**: zsiga/agent/loop.py::_extract_tool_calls_from_content
- **Given** content contains explanatory text before and after an inline JSON tool call object
- **When** `_extract_tool_calls_from_content(content)` is called
- **Then** it SHALL still extract the tool call tuple from within the surrounding text

### Requirement: Fallback Only Executes Registered Tools

When the fallback parser extracts tool calls, the AgentLoop MUST only execute tools whose names exist in the registered tool functions (`self.tool_funcs`). Extracted tool calls referencing unregistered tool names SHALL be silently skipped. This prevents the parser from accidentally executing unregistered operations due to false-positive matches on ordinary text.

#### Scenario: Unregistered tool name is skipped during execution

- **testable**: false
- **Given** the fallback parser extracts a tool call with name `dangerous_tool` which is not in `self.tool_funcs`
- **When** the AgentLoop processes the extracted tool calls
- **Then** that tool call SHALL be skipped — not passed to any execution path — and processing SHALL continue with any remaining extracted calls

### Requirement: Turn Loop Continuation on Fallback Success

When the fallback parser successfully extracts at least one registered tool call, the AgentLoop SHALL execute those tool calls and continue the turn loop. It MUST NOT return a `RunResult` in this case. Only when extraction yields zero executable tool calls SHALL the response be treated as a final answer and a `RunResult` returned.

#### Scenario: Fallback extraction continues turn loop

- **testable**: false
- **Given** an AgentLoop turn receives a message with empty `tool_calls` and content containing a registered tool call pattern
- **When** the fallback parser extracts at least one registered tool call
- **Then** the agent loop SHALL execute the extracted tool calls, append results to the conversation, and continue to the next turn iteration

#### Scenario: Fallback failure returns RunResult as final response

- **testable**: false
- **Given** an AgentLoop turn receives a message with empty `tool_calls` and content with no extractable tool call patterns
- **When** `_extract_tool_calls_from_content` returns an empty list
- **Then** the agent loop SHALL return a `RunResult` with the message content as the final response (unchanged behavior from current code)

### Requirement: Fallback Activation Warning

When the fallback parser is triggered (because `msg.tool_calls` is empty and content parsing is attempted), the system SHALL log a WARNING-level message. This ensures non-standard LLM output format is observable in production logs for monitoring and debugging.

#### Scenario: Warning logged when fallback parsing succeeds

- **testable**: false
- **Given** `msg.tool_calls` is empty and `_extract_tool_calls_from_content` returns at least one tool call
- **When** the AgentLoop processes the fallback result
- **Then** a WARNING log entry SHALL be emitted containing the phrase "fallback tool call parsed"

#### Scenario: No warning when tool_calls is populated normally

- **testable**: false
- **Given** `msg.tool_calls` contains one or more standard tool call objects
- **When** the AgentLoop processes the message
- **Then** no fallback-related warning SHALL be logged (the normal `tool_calls` path is used exclusively)
