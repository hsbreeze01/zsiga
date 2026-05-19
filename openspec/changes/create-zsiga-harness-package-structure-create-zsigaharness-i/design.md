# Design: zsiga Harness Package Structure

## Architecture Decision

Create a new sub-package `zsiga/harness/` that serves as the foundation for a 4-layer test harness system. This layer (Layer 1) provides:

1. **Package entry point** (`__init__.py`) — re-exports public API
2. **Mock fixtures** (`conftest.py`) — deterministic test doubles for LLM client, transport, and git
3. **Test runner** (`runner.py`) — discovers tests, runs them, collects structured events

### Why a separate sub-package?
- Clean separation from runtime `zsiga` code
- Can be extended independently (Layers 2–4 will add more modules)
- Standard Python package convention makes discovery and import predictable

## Data Flow

```
HarnessRunner.discover(path) → list[test_file]
        │
        ▼
HarnessRunner.run()
   ├── creates test context with fixtures
   ├── executes each test file
   ├── emits events: TestStarted → TestPassed | TestFailed
   └── aggregates into HarnessResult(counts, events)
```

### Event types (dataclasses)

```
TestEvent
  ├── TestStarted(test_name, timestamp)
  ├── TestPassed(test_name, timestamp, duration_ms)
  ├── TestFailed(test_name, timestamp, duration_ms, error_message)
  └── TestError(test_name, timestamp, error_message)

HarnessResult
  ├── total: int
  ├── passed: int
  ├── failed: int
  ├── errors: int
  └── events: list[TestEvent]
```

### Fixture interfaces

```
MockLLMClient
  ├── chat(prompt: str) → str
  ├── set_response(text: str) → None
  └── calls: list[tuple[str, ...]]  # recorded calls

MockTransport
  ├── call(tool_name: str, args: dict) → dict
  ├── set_result(result: dict) → None
  └── recorded: list[tuple[str, dict]]

TempGitRepo
  ├── path: Path
  ├── git(*args) → subprocess result
  └── cleanup() → None  # auto-called via finalizer
```

## Files to Create

| File | Purpose |
|------|---------|
| `zsiga/harness/__init__.py` | Package init; re-exports `HarnessRunner`, `HarnessResult`, event classes, fixture functions |
| `zsiga/harness/conftest.py` | `mock_llm_client`, `mock_transport`, `temp_git_repo` fixture implementations |
| `zsiga/harness/runner.py` | `HarnessRunner` class with `discover()` and `run()`; event/result dataclasses |

## Dependencies

- `unittest.mock` (stdlib) — for mocking LLM client and transport
- `subprocess` (stdlib) — for temp git repo creation
- `tempfile` (stdlib) — for isolated directories
- `pathlib` (stdlib) — for path handling
- `dataclasses` (stdlib) — for structured events
- `time` (stdlib) — for timing measurements
- `importlib` (stdlib) — for dynamic test module loading

No new external dependencies required.

## Testing Strategy

Tests for the harness itself will live in `tests/test_harness_runner.py`, `tests/test_harness_conftest.py` — using the project's existing pytest setup.
