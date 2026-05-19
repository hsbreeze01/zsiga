# Design: pipeline/dependency.py — ChangeGraph

## Architecture Decision

Create a new module `pipeline/dependency.py` containing a single `ChangeGraph` class. This module is standalone — it depends only on the Python standard library (`pathlib`, `re`, collections from `typing`). No external dependencies.

### Why a dedicated module?
- Separation of concerns: dependency analysis is a distinct pipeline concern.
- Testability: `tests/test_dependency.py` already exists, confirming this is the expected location.

## Data Flow

```
openspec_dir/changes/<name>/proposal.md
        │
        ▼
  add_change(name)
        │  reads proposal.md → extracts target files
        ▼
  _changes: dict[str, list[str]]   # change_name → [target_files]
        │
        ├─► check_conflicts()
        │     pairwise intersection of target file sets
        │
        └─► execution_order()
              build DAG (edge: shared target file, tie-break by name)
              topological sort via Kahn's algorithm
```

## Target File Extraction Strategy

The `add_change` method parses `proposal.md` to find target file references. Files are identified by matching paths that look like source files (e.g., `src/...`, `pipeline/...`, `tests/...` — lines containing a `/` and a known extension like `.py`, `.md`, `.html`, `.toml`, `.yaml`, `.yml`, `.json`).

A simpler and more robust approach: extract all lines matching `r'^\s*[-*]\s+` (a list item in Markdown) that contain a file-like path (contain `/` or end with a known extension). This covers the common case of proposal.md listing target files as a bullet list.

## Conflict Detection

For `check_conflicts()`:
- Convert each change's target list to a `set`.
- Compare every pair `(i, j)` where `i < j` (by name).
- Record conflicts as `(name_i, name_j, sorted(list(intersection)))`.

## Topological Sort

For `execution_order()`:
- Build adjacency list: for each conflicting pair, add a directed edge from the lexicographically earlier name to the later one.
- Use Kahn's algorithm (BFS with in-degree tracking).
- If the sorted output has fewer nodes than the total registered changes → cycle exists → raise `CycleError`.

## Exception Class

Define a simple `CycleError(Exception)` in the same module for cycle detection in topological sort.

## File List

| Action | Path |
|--------|------|
| CREATE | `pipeline/dependency.py` |
| CREATE | `pipeline/__init__.py` (if not exists) |

No modifications to existing files. The existing `tests/test_dependency.py` will need to be extended or verified against this implementation (separate task).
