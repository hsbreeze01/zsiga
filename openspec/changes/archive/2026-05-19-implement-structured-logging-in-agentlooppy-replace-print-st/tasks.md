# Tasks: Structured Logging

## Group 1: Logging Infrastructure

- [x] 1.1 Create `zsiga/logging.py` — `LogConfig` dataclass, `TextFormatter`, `JsonFormatter`, and `setup_logging()` function
- [x] 1.2 Add `LoggingConfig` to `zsiga/config.py` — parse `logging` section from yaml, wire into `ZsigaConfig` and `load_config()`
- [x] 1.3 Add unit tests for logging module — `TextFormatter` output, `JsonFormatter` JSON validity, `setup_logging()` configuration, `LoggingConfig` parsing

## Group 2: Replace print() in Agent Loop

- [x] 2.1 Replace all `print()` in `zsiga/agent/loop.py` with structured `log.info/debug/warning` calls, preserving phase labels and emoji prefixes in message text

## Group 3: Replace print() in Pipeline Modules

- [ ] 3.1 Replace all `print()` in `zsiga/pipeline/orchestrator.py` with structured `log.info/warning/error` calls — phase boundaries, fix attempts, verdicts, reverts, diagnosis
- [ ] 3.2 Replace all `print()` in `zsiga/pipeline/enricher.py`, `zsiga/pipeline/utils.py`, `zsiga/agent/sub_agent.py`, and `zsiga/git_ops.py` with appropriate `log` calls

## Group 4: Application Startup Integration

- [ ] 4.1 Wire `setup_logging()` into `zsiga/__main__.py` `main()` — call before any other module logic; add integration test verifying `AgentLoop` emits correct log records via `caplog`
