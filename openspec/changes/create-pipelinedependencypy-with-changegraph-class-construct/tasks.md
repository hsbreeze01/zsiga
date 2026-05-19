# Tasks: pipeline/dependency.py — ChangeGraph

## 1. Core Module

- [x] **1.1** Create `pipeline/__init__.py` (empty, if not present) and `pipeline/dependency.py` with `CycleError` exception class and `ChangeGraph` class skeleton (constructor validates directory, initializes `_changes: dict[str, list[str]]`)
- [x] **1.2** Implement `add_change(change_name)` — read `proposal.md` from the change directory, parse target file paths from Markdown bullet-list lines, register change; raise `FileNotFoundError` if missing, `ValueError` on duplicate
- [x] **1.3** Implement `check_conflicts()` — pairwise set intersection over registered changes' target lists, return `list[tuple[str, str, list[str]]]`
- [x] **1.4** Implement `execution_order()` — build DAG from conflict pairs (edge direction: lexicographic name order), Kahn's algorithm topological sort, raise `CycleError` on cycle

## 2. Validation

- [x] **2.1** Run existing `tests/test_dependency.py` against the new implementation and fix any failures; ensure ruff passes on `pipeline/dependency.py`
