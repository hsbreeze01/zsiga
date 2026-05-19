# Delta Spec: Structured Logging

## ADDED Requirements

### REQ-LOG-01: Structured Log Output

The agent loop and pipeline modules SHALL emit log messages through Python's
`logging` module instead of `print()` statements.

#### Scenario: Agent loop emits structured log on start

- **Given** an `AgentLoop` instance with phase label "enrich"
- **When** `run()` is invoked with `max_turns=10` and `timeout_seconds=300`
- **Then** a `logging.INFO` message SHALL be emitted containing keys
  `phase`, `max_turns`, and `timeout_seconds`
- **And** no `print()` call SHALL be made

#### Scenario: Agent loop emits structured log on timeout

- **Given** an `AgentLoop` in progress with phase label "impl"
- **When** the elapsed time exceeds `timeout_seconds`
- **Then** a `logging.WARNING` message SHALL be emitted containing keys
  `phase`, `turn`, `elapsed_seconds`, `llm_calls`, and `tool_calls`

#### Scenario: Agent loop emits structured log on tool invocation

- **Given** an `AgentLoop` in progress with phase label "verify"
- **When** a tool call is executed
- **Then** a `logging.DEBUG` message SHALL be emitted containing keys
  `phase`, `turn`, `tool_name`, and `args_preview`

---

### REQ-LOG-02: Log Level Hierarchy

All log messages SHALL be assigned one of the standard Python log levels
based on semantic meaning:

| Level | Usage |
|-------|-------|
| `DEBUG` | Tool invocations, tool result metadata, compaction events |
| `INFO` | Phase start/end, cycle start/end, context loading, git operations |
| `WARNING` | Timeouts, max turns reached, mechanical verification failures |
| `ERROR` | Reverts, escalation aborts, diagnosis failures |

#### Scenario: Phase boundary logged at INFO level

- **Given** the orchestrator is about to enter Phase 2 (IMPLEMENT)
- **When** the phase header is printed
- **Then** a `logging.INFO` message SHALL be emitted with `phase="implement"` and `change_name`

#### Scenario: Max turns reached logged at WARNING level

- **Given** an `AgentLoop` has exhausted its `max_turns` budget
- **When** the loop terminates without a final message
- **Then** a `logging.WARNING` message SHALL be emitted with `phase`, `max_turns`, and `elapsed_seconds`

---

### REQ-LOG-03: JSON Format Support

The logging system SHALL support a JSON formatter that outputs one JSON
object per log line for machine parsing.

#### Scenario: JSON log line is valid JSON

- **Given** the logging configuration sets `format: json`
- **When** any log message is emitted
- **Then** each line of output SHALL be a valid JSON object
- **And** the object SHALL contain keys `timestamp`, `level`, `logger`, `message`
- **And** any structured context SHALL be nested under a `context` key

#### Scenario: JSON log includes structured context

- **Given** the JSON formatter is active
- **When** the agent loop logs a tool invocation with `tool_name="bash"` and `args_preview="ls -la"`
- **Then** the output JSON SHALL contain `"context": {"tool_name": "bash", "args_preview": "ls -la", ...}`

---

### REQ-LOG-04: Configuration via zsiga.yaml

Logging behavior SHALL be configurable through a top-level `logging` section
in `zsiga.yaml`.

#### Scenario: Default logging configuration (no logging section)

- **Given** a `zsiga.yaml` file with no `logging` section
- **When** the application starts
- **Then** the root logger SHALL use level `INFO`
- **And** the format SHALL be human-readable text (not JSON)
- **And** output SHALL go to `stderr`

#### Scenario: JSON logging configured

- **Given** a `zsiga.yaml` file with `logging.format: json`
- **When** the application starts
- **Then** all log output SHALL use JSON format

#### Scenario: Debug level configured

- **Given** a `zsiga.yaml` file with `logging.level: DEBUG`
- **When** the application starts
- **Then** the root logger SHALL be set to `DEBUG` level
- **And** `DEBUG`-level messages SHALL appear in output

#### Scenario: Log file configured

- **Given** a `zsiga.yaml` file with `logging.file: /var/log/zsiga.log`
- **When** the application starts
- **Then** log output SHALL be written to that file path
- **And** output SHALL also appear on `stderr` (dual handler)

---

### REQ-LOG-05: Logger Hierarchy

Each module SHALL obtain its own named logger via `logging.getLogger(__name__)`.
The logger names SHALL follow the Python module path convention.

#### Scenario: Agent loop uses module-scoped logger

- **Given** the module `zsiga.agent.loop`
- **When** any log message is emitted from that module
- **Then** the logger name SHALL be `"zsiga.agent.loop"`

#### Scenario: Orchestrator uses module-scoped logger

- **Given** the module `zsiga.pipeline.orchestrator`
- **When** any log message is emitted from that module
- **Then** the logger name SHALL be `"zsiga.pipeline.orchestrator"`

---

### REQ-LOG-06: Backward Compatibility

When `logging.level` is `INFO` or higher and `logging.format` is `text`
(or absent), the console output SHALL remain visually similar to the current
print-based output, preserving phase labels, emoji prefixes, and indentation.

#### Scenario: Text format preserves visual style

- **Given** the default text logging format
- **When** the agent loop starts with phase "impl"
- **Then** the output line SHALL contain `  [impl]` as a prefix
- **And** the output SHALL be visually similar to the previous `print()` output

---

### REQ-LOG-07: Logging Initialization

A `setup_logging()` function SHALL be provided that reads configuration and
configures the root logger. This function SHALL be called once at application
startup, before any log messages are emitted.

#### Scenario: setup_logging called on startup

- **Given** the application entry point `zsiga.__main__`
- **When** `main()` is invoked
- **Then** `setup_logging()` SHALL be called before any other module logic
- **And** all subsequent log messages SHALL use the configured format and level
