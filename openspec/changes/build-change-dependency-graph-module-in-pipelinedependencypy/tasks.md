# Tasks: Change Dependency Graph Module

## 1. Data Models and Core Graph

- [x] **1.1** Add `ConflictEdge` and `DependencyGraph` dataclasses + `_parse_depends_on()` helper + `build_dependency_graph()` function in `zsiga/pipeline/dependency.py`
  - Add `ConflictEdge` dataclass (from_id, to_id, conflict_type, severity, shared_files)
  - Add `DependencyGraph` dataclass (nodes dict, adjacency dict, edges list)
  - Add `_parse_depends_on(tasks_content: str) -> list[str]` to parse `<!-- depends-on: ... -->` from tasks.md
  - Add `build_dependency_graph(changes: list[ChangeInfo], transport=None) -> DependencyGraph` that reads tasks.md for each change, builds adjacency from explicit deps + file overlaps, assigns severity
  - Add cycle detection (DFS three-color) that raises `ValueError` with cycle path
  - Pre-estimated: 2 rounds (read existing file + write additions + verify lint)

## 2. Topological Sort and Conflict Report

- [x] **2.1** Add `topological_order()` and `conflict_report()` methods to `DependencyGraph` in `zsiga/pipeline/dependency.py`
  - `DependencyGraph.topological_order() -> list[str]` using Kahn's algorithm with tiebreak (fewer target files → lexicographic id)
  - `DependencyGraph.conflict_report() -> str` producing human-readable summary of all conflicts and execution order
  - Pre-estimated: 1 round (write + verify lint)

## 3. Integration Method on Detector

- [x] **3.1** Add `build_graph()` convenience method to `ChangeConflictDetector` in `zsiga/pipeline/dependency.py`
  - `ChangeConflictDetector.build_graph(changes_dir: str) -> DependencyGraph` — scans changes then builds graph in one call
  - Pre-estimated: 1 round (write + verify lint)

## 4. Tests

- [x] **4.1** Add test classes for all new dependency graph scenarios in `tests/test_dependency.py`
  - `TestBuildDependencyGraph` — graph construction with overlaps, no overlaps, cycle detection
  - `TestParseDependsOn` — parse HTML comment declarations, no declarations, multiple declarations
  - `TestConflictSeverity` — HIGH for .py, LOW for .md, mixed extensions
  - `TestTopologicalOrder` — explicit deps respected, tiebreak behavior, independent changes deterministic
  - `TestConflictReport` — full report with conflicts, clean report with no conflicts
  - `TestBuildGraphIntegration` — end-to-end via `ChangeConflictDetector.build_graph()` with temp directory
  - Pre-estimated: 2 rounds (write tests + run and fix)
