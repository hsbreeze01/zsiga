# Tasks: zsiga Harness Package Structure

## 1. Package Scaffolding

- [x] Create `zsiga/harness/__init__.py` with re-exports of `HarnessRunner`, `HarnessResult`, event dataclasses (`TestStarted`, `TestPassed`, `TestFailed`, `TestError`), and fixture references (`mock_llm_client`, `mock_transport`, `temp_git_repo`)

## 2. Mock Fixtures (conftest.py)

- [x] Implement `MockLLMClient` class with `chat()`, `set_response()`, and call recording in `zsiga/harness/conftest.py`
- [x] Implement `MockTransport` class with `call()`, `set_result()`, and call recording in `zsiga/harness/conftest.py`
- [x] Implement `TempGitRepo` class with `path`, `git()`, auto-cleanup via `__del__`/context manager, and optional initial commit in `zsiga/harness/conftest.py`
- [x] Expose `mock_llm_client`, `mock_transport`, `temp_git_repo` as factory functions (returning instances) in `zsiga/harness/conftest.py`

## 3. Harness Runner (runner.py)

- [x] Implement event dataclasses (`TestStarted`, `TestPassed`, `TestFailed`, `TestError`) and `HarnessResult` in `zsiga/harness/runner.py`
- [x] Implement `HarnessRunner` class with `discover(path)` (glob `test_*.py`), `run()` (load & exec each test module, capture results into events), and `results` property in `zsiga/harness/runner.py`

## 4. Tests

- [x] Add `tests/test_harness_conftest.py` — verify `MockLLMClient` response/config/call-recording, `MockTransport` call/recording, `TempGitRepo` creation/cleanup/initial-commit
- [x] Add `tests/test_harness_runner.py` — verify `discover()` finds test files, `run()` emits correct events, `HarnessResult` aggregates counts correctly
