# Tasks: Change Conflict Detector

## Group 1: Data Models and Core Class

- [x] 1.1 Create `zsiga/pipeline/dependency.py` with `ChangeInfo` and `ConflictPair` dataclasses, plus `ChangeConflictDetector` class skeleton with `scan_changes`, `find_overlaps`, and `suggest_order` method stubs

- [x] 1.2 Implement `scan_changes` method — list change subdirectories, parse each `design.md` for target files via regex, return `list[ChangeInfo]`

- [x] 1.3 Implement `find_overlaps` method — pairwise set intersection of target_files, return `list[ConflictPair]` for every non-empty intersection

- [x] 1.4 Implement `suggest_order` method — sort changes by overlap count ascending, tiebreak by change id lexicographic

## Group 2: Tests

- [x] 2.1 Create `tests/test_dependency.py` with tests for all CCD-01 through CCD-04 scenarios: scan_changes (multiple/empty/missing-design), find_overlaps (shared/disjoint/three-way/empty-targets), suggest_order (fewer-deps-first/overlaps-after/all-overlap/single), and target file extraction (with-paths/no-paths/dedup)
