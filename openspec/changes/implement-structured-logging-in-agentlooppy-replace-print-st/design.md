# Design: Structured Logging

## Architecture Decision

Replace all `print()` calls across the zsiga codebase with Python's standard
`logging` module, using structured context via `extra` kwargs. Provide a
single `setup_logging()` function that configures formatters, handlers, and
log levels based on `zsiga.yaml`.

**Why `logging` over alternatives (loguru, structlog)?**
- Zero additional dependencies (project uses only stdlib + yaml + httpx)
- `logging` is the standard Python approach; all existing code patterns align
- JSON output achieved via a custom `logging.Formatter` subclass (~30 lines)

## Data Flow

```
zsiga.yaml (logging section)
    ↓
setup_logging(config)
    ├── creates StreamHandler(stderr) with TextFormatter or JsonFormatter
    ├── optionally creates FileHandler(logging.file)
    └── sets root logger level
    ↓
Module-level: log = logging.getLogger(__name__)
    ↓
log.info("message", extra={"phase": "impl", "turn": 3, ...})
    ↓
Formatter formats → stderr (and optional file)
```

## Configuration Schema

New top-level key in `zsiga.yaml`:

```yaml
logging:
  level: INFO          # DEBUG | INFO | WARNING | ERROR
  format: text         # text | json
  file: null           # optional file path for dual output
```

All fields are optional. Defaults: `level=INFO`, `format=text`, `file=null`.

## Files to Create

| File | Purpose |
|------|---------|
| `zsiga/logging.py` | `setup_logging()`, `TextFormatter`, `JsonFormatter`, `LogConfig` dataclass |

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/config.py` | Add `LoggingConfig` class; parse `logging` section from yaml; add `logging` field to `ZsigaConfig` |
| `zsiga/__main__.py` | Call `setup_logging()` early in `main()`; replace `print()` with `log.info/warning` |
| `zsiga/agent/loop.py` | Replace all `print()` with `log.debug/info/warning`; add structured `extra` context |
| `zsiga/agent/sub_agent.py` | Replace all `print()` with `log.info/debug` |
| `zsiga/pipeline/orchestrator.py` | Replace all `print()` with `log.info/warning/error` |
| `zsiga/pipeline/enricher.py` | Replace `print()` with `log.warning` |
| `zsiga/pipeline/utils.py` | Replace `print()` with `log.info/warning` |
| `zsiga/git_ops.py` | Replace `print()` with `log.info` |

## Key Design Decisions

### 1. TextFormatter preserves visual style

The custom `TextFormatter` will format messages to closely match the current
`print()` output. For messages that previously used emoji prefixes like
`✅`, `⚠️`, `🔧`, these will be preserved in the message text.

Format template:
```
  [%(phase)s] %(message)s
```

Where `phase` is passed via `extra`. For non-phase messages, the formatter
falls back to the raw message.

### 2. JsonFormatter produces one JSON object per line

```json
{"timestamp":"2024-01-15T10:30:00.123Z","level":"INFO","logger":"zsiga.agent.loop","message":"done","context":{"phase":"impl","elapsed_seconds":12.3}}
```

### 3. No dependency changes

All implementation uses Python stdlib `logging`, `json`, and `datetime`.
No new packages in `requirements.txt`.

### 4. LogConfig integrates with existing config pattern

Follows the same pattern as `CompactionConfig`, `PipelineConfig`, etc.:
plain class with `__init__` defaults, parsed in `load_config()`.

### 5. __main__.py prints preserved for CLI user-facing output

CLI command outputs (`cmd_status`, `cmd_projects`, `cmd_log`, `cmd_dashboard`,
`cmd_propose`) use `print()` intentionally for user-facing terminal output.
These SHALL NOT be converted to logging — they are command-line UI, not
operational logging. The rule: if a `print()` is inside a `cmd_*` function
that formats tabular/output for a human user, keep it as `print()`.
Operational/internal prints (phase markers, tool calls, metrics) convert to logging.

### 6. Test Strategy

- Unit tests for `TextFormatter` and `JsonFormatter` output format
- Unit test for `setup_logging()` configuration
- Unit test for `LoggingConfig` parsing from yaml
- Integration test: verify `AgentLoop.run()` emits correct log records
  via `caplog` fixture
