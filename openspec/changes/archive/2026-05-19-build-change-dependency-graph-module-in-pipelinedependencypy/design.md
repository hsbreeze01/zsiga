# Design: Change Dependency Graph Module

## Architecture Decision

Extend the existing `zsiga/pipeline/dependency.py` module (which already has `ChangeInfo`, `ConflictPair`, and `ChangeConflictDetector`) with a proper **graph-based** dependency model. The existing `ChangeConflictDetector` is preserved for backward compatibility; new capabilities are built on top.

### Key Design Choices

1. **Directed Acyclic Graph (DAG)**: Use an adjacency-list representation (`dict[str, set[str]]`) to model change dependencies. Edges represent either explicit `depends-on` declarations or implicit file-overlap ordering.

2. **Cycle Detection via DFS**: Use a standard three-color DFS (white/grey/black) to detect cycles during graph construction. If a cycle is found, raise `ValueError` with the cycle path.

3. **Conflict Severity**: Classify by file extension — `.py` overlaps are HIGH, `.md` overlaps are LOW. This is a simple heuristic that matches the project's primary concern (Python code changes are riskier to merge concurrently).

4. **Topological Sort**: Kahn's algorithm (BFS-based) for deterministic ordering. Tiebreak by: fewer target files first → lexicographic change ID. This ensures stable, predictable output.

5. **Explicit Dependencies**: Parse `<!-- depends-on: id1, id2 -->` HTML comments from `tasks.md`. This is a lightweight, non-invasive convention that doesn't require new file formats.

6. **Backward Compatibility**: Existing `ChangeConflictDetector`, `ChangeInfo`, `ConflictPair`, and all test scenarios (CCD-01 through CCD-04) remain unchanged. New classes and functions are additive.

## Data Flow

```
openspec/changes/
  ├── change-a/
  │   ├── design.md   ──parse──→ target_files (existing _extract_target_files)
  │   └── tasks.md    ──parse──→ explicit dependencies (new _parse_depends_on)
  ├── change-b/
  │   └── ...
  └── ...

ChangeConflictDetector.scan_changes() → list[ChangeInfo]
     │
     ▼
build_dependency_graph(changes) → DependencyGraph
     │  ├── edges from file overlaps (existing logic + severity)
     │  └── edges from explicit depends-on
     ▼
DependencyGraph.topological_order() → list[str]
DependencyGraph.detect_cycles() → raises ValueError
DependencyGraph.conflict_report() → str
```

## Data Models

### New Classes (in `zsiga/pipeline/dependency.py`)

```python
@dataclass
class ConflictEdge:
    """A directed edge representing a conflict/dependency between two changes."""
    from_id: str
    to_id: str
    conflict_type: str        # "file_overlap" | "explicit_dep"
    severity: str             # "HIGH" | "LOW" | "NONE"
    shared_files: list[str]   # empty for explicit deps

@dataclass
class DependencyGraph:
    """DAG of change dependencies."""
    nodes: dict[str, ChangeInfo]               # id → ChangeInfo
    adjacency: dict[str, set[str]]             # from_id → {to_id, ...}
    edges: list[ConflictEdge]                  # all edges with metadata
```

### Modified Data

- `ChangeConflictDetector` gains a `build_graph()` method that returns a `DependencyGraph`
- New standalone functions: `build_dependency_graph()`, `_parse_depends_on()`

## Files to Add/Modify

| File | Action | Description |
|------|--------|-------------|
| `zsiga/pipeline/dependency.py` | MODIFY | Add `ConflictEdge`, `DependencyGraph`, `_parse_depends_on()`, `build_dependency_graph()`, topological sort, cycle detection, conflict report |
| `tests/test_dependency.py` | MODIFY | Add test classes for all new scenarios (graph construction, explicit deps, severity, topological order, conflict report) |
