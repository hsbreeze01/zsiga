# Tasks: Dependency Tracking Integration in pipeline/utils.py

## 1. Backend — Utility Functions

- [x] 1.1 Add `ConflictResult` dataclass and three integration functions (`detect_change_conflicts`, `suggest_merge_order`, `warn_change_conflicts`) to `zsiga/pipeline/utils.py` with imports from `.dependency`
- [x] 1.2 Add tests for the three new utils functions in `tests/test_dependency.py` — covering: conflicts found, no conflicts, missing changes directory, merge order correctness, warning string format, and None return for clean state

## 2. Verification

- [x] 2.1 Run `ruff check` and `pytest` on modified files to ensure all tests pass and code is lint-clean
