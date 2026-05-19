# Spec: Dependency Tracking Integration in pipeline/utils.py

## ADDED Requirements

### Requirement: Scan Cross-Change File Conflicts

The system SHALL provide a function `detect_change_conflicts(target_path)` in `zsiga/pipeline/utils.py` that scans the `openspec/changes/` directory of the target project, parses each pending change's `design.md` for target file paths, and returns a structured conflict report.

#### Scenario: Multiple pending changes share a target file
- Given a target project at `target_path` with two pending changes in `openspec/changes/`
- And change-A's `design.md` references `zsiga/pipeline/utils.py`
- And change-B's `design.md` also references `zsiga/pipeline/utils.py`
- When `detect_change_conflicts(target_path)` is called
- Then the result SHALL contain a conflict entry listing both change IDs and the shared file `zsiga/pipeline/utils.py`
- And the conflict severity SHALL be `HIGH` because the shared file is a `.py` file

#### Scenario: No shared files across pending changes
- Given a target project with three pending changes in `openspec/changes/`
- And no two changes reference the same target file
- When `detect_change_conflicts(target_path)` is called
- Then the result SHALL indicate zero conflicts detected

#### Scenario: Changes directory does not exist
- Given a target project with no `openspec/changes/` directory
- When `detect_change_conflicts(target_path)` is called
- Then the function SHALL return a result indicating zero changes scanned and zero conflicts

### Requirement: Merge Order Suggestions

The system SHALL provide a function `suggest_merge_order(target_path)` in `zsiga/pipeline/utils.py` that returns an ordered list of change IDs representing the recommended execution sequence.

#### Scenario: Overlapping changes ordered by dependency
- Given change-A and change-B both target `zsiga/pipeline/utils.py`
- When `suggest_merge_order(target_path)` is called
- Then the result SHALL be an ordered list of change IDs
- And changes with fewer target files SHALL appear before changes with more target files
- And the list SHALL respect explicit `depends-on` declarations from `tasks.md`

#### Scenario: All changes independent
- Given three pending changes with no overlapping target files and no explicit dependencies
- When `suggest_merge_order(target_path)` is called
- Then the result SHALL order changes lexicographically by change ID

### Requirement: Conflict Warning Report

The system SHALL provide a function `warn_change_conflicts(target_path)` in `zsiga/pipeline/utils.py` that returns a human-readable warning string if conflicts exist, or `None` if no conflicts are detected.

#### Scenario: Conflicts detected produce warning string
- Given two changes that share `zsiga/pipeline/utils.py`
- When `warn_change_conflicts(target_path)` is called
- Then the return value SHALL be a non-None string containing:
  - The severity level (`HIGH` for `.py` overlaps)
  - The names of the conflicting changes
  - The shared file paths
  - A suggested execution order

#### Scenario: No conflicts returns None
- Given pending changes with no file overlaps
- When `warn_change_conflicts(target_path)` is called
- Then the return value SHALL be `None`

### Requirement: Dependency Module Integration

All three functions SHALL delegate to the existing `zsiga/pipeline/dependency.py` module (`ChangeConflictDetector`, `build_dependency_graph`, `DependencyGraph.conflict_report`) rather than reimplementing conflict detection logic.

#### Scenario: Functions use the dependency module
- Given the existing `ChangeConflictDetector` and `build_dependency_graph` in `dependency.py`
- When `detect_change_conflicts` is called
- Then it SHALL internally call `ChangeConflictDetector.scan_changes()` and `ChangeConflictDetector.find_overlaps()`
- When `suggest_merge_order` is called
- Then it SHALL internally call `build_dependency_graph()` and `DependencyGraph.topological_order()`
- When `warn_change_conflicts` is called
- Then it SHALL internally call `build_dependency_graph()` and `DependencyGraph.conflict_report()`
