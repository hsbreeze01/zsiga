# Design: Dependency Tracking Integration in pipeline/utils.py

## Architecture Decision

Add three high-level convenience functions to `zsiga/pipeline/utils.py` that serve as the public API for change dependency tracking. These functions delegate entirely to the existing `zsiga/pipeline/dependency.py` module, which already contains `ChangeConflictDetector`, `DependencyGraph`, `build_dependency_graph()`, and related dataclasses.

**Rationale:** The `dependency.py` module contains the full implementation and is well-tested via `tests/test_dependency.py`. Adding wrapper functions in `utils.py` provides a simpler, single-call API for orchestrator code and the main agent loop without duplicating logic.

## Data Flow

```
target_path
  │
  ├─► detect_change_conflicts(target_path)
  │     └─► ChangeConflictDetector().scan_changes(changes_dir)
  │     └─► ChangeConflictDetector().find_overlaps(changes)
  │     └─► returns ConflictResult dataclass
  │
  ├─► suggest_merge_order(target_path)
  │     └─► ChangeConflictDetector().scan_changes(changes_dir)
  │     └─► build_dependency_graph(changes)
  │     └─► DependencyGraph.topological_order()
  │     └─► returns list[str]
  │
  └─► warn_change_conflicts(target_path)
        └─► ChangeConflictDetector().scan_changes(changes_dir)
        └─► build_dependency_graph(changes)
        └─► DependencyGraph.conflict_report()
        └─► returns str | None
```

## New Types

```python
@dataclass
class ConflictResult:
    change_count: int                    # total pending changes scanned
    conflicts: list[ConflictPair]        # from dependency.py
    has_high_severity: bool              # True if any .py file overlap exists
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/pipeline/utils.py` | Add `ConflictResult` dataclass, `detect_change_conflicts()`, `suggest_merge_order()`, `warn_change_conflicts()` |
| `tests/test_dependency.py` | Add test classes for the three new utils functions |

## Implementation Notes

1. The `changes_dir` path is computed as `f"{target_path}/openspec/changes"` — consistent with existing code in `utils.py` (see `archive_change`) and `__main__.py`.
2. If the `changes_dir` does not exist or `scan_changes` returns empty, all three functions return safe defaults (empty `ConflictResult`, empty list, `None`).
3. Import from `.dependency` at module level to avoid circular imports (dependency.py already imports from .utils, but only `read_file` which is defined early).
4. No frontend changes needed — these are backend utility functions only.
