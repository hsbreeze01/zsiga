# Change Conflict Detector

## ADDED Requirements

### Requirement: CCD-01 — Scan Pending Changes

The system SHALL provide a `ChangeConflictDetector` class that scans an
openspec changes directory and returns a list of pending change descriptors.

#### Scenario: Multiple pending changes found

- **Given** an openspec `changes/` directory containing 3 subdirectories,
  each with a `proposal.md`, `design.md`, and `tasks.md`
- **When** `scan_changes(changes_dir)` is called
- **Then** it SHALL return a list of 3 `ChangeInfo` entries, each containing
  at minimum the change `id` (directory name) and the set of `target_files`
  parsed from its `design.md`

#### Scenario: Empty changes directory

- **Given** an openspec `changes/` directory with no subdirectories (or only an
  `archive/` folder)
- **When** `scan_changes(changes_dir)` is called
- **Then** it SHALL return an empty list without error

#### Scenario: Change directory missing design.md

- **Given** an openspec change subdirectory that has `proposal.md` but no
  `design.md`
- **When** `scan_changes(changes_dir)` is called
- **Then** the change SHALL still be included in the result with an empty
  `target_files` set

### Requirement: CCD-02 — Find File Overlaps

The system SHALL provide a `find_overlaps` method that identifies pairs of
pending changes that target the same file(s).

#### Scenario: Two changes share one target file

- **Given** two pending changes where Change A targets
  `["zsiga/pipeline/utils.py", "zsiga/pipeline/diagnoser.py"]` and Change B
  targets `["zsiga/pipeline/utils.py", "tests/test_foo.py"]`
- **When** `find_overlaps(changes)` is called
- **Then** it SHALL return a list containing one `ConflictPair` with
  `change_ids = ("A", "B")` and `shared_files = ["zsiga/pipeline/utils.py"]`

#### Scenario: No overlapping files across changes

- **Given** three pending changes with disjoint target file sets
- **When** `find_overlaps(changes)` is called
- **Then** it SHALL return an empty list

#### Scenario: Three changes all share one file

- **Given** changes A, B, C all target `"zsiga/pipeline/utils.py"`
- **When** `find_overlaps(changes)` is called
- **Then** it SHALL return three `ConflictPair` entries:
  (A, B), (A, C), and (B, C), each listing `"zsiga/pipeline/utils.py"` in
  `shared_files`

#### Scenario: Changes with empty target_files are ignored

- **Given** a change whose `target_files` set is empty
- **When** `find_overlaps(changes)` is called
- **Then** that change SHALL NOT appear in any conflict pair

### Requirement: CCD-03 — Suggest Execution Order

The system SHALL provide a `suggest_order` method that returns an ordered
list of change IDs representing the recommended execution priority, based on
a dependency graph derived from file relationships.

#### Scenario: Independent changes sorted by dependency count

- **Given** Change A targets 3 files, Change B targets 1 file, and no overlaps
  exist
- **When** `suggest_order(changes)` is called
- **Then** it SHALL return change IDs ordered such that changes with fewer
  dependencies (fewer files touched) come first: [B, A]

#### Scenario: Overlapping changes are ordered after non-overlapping

- **Given** changes A (no overlaps), B (overlaps with C), and C (overlaps
  with B)
- **When** `suggest_order(changes)` is called
- **Then** A SHALL appear before both B and C in the result

#### Scenario: All changes overlap

- **Given** 4 changes where every pair has at least one shared file
- **When** `suggest_order(changes)` is called
- **Then** it SHALL return a deterministic ordering (sorted by change id as
  tiebreaker) of all 4 changes

#### Scenario: Single change

- **Given** exactly one pending change
- **When** `suggest_order(changes)` is called
- **Then** it SHALL return a list containing only that change's id

### Requirement: CCD-04 — Target Files Extraction

The system SHALL parse `design.md` files to extract target file paths listed
in a "files to add/modify" section.

#### Scenario: Design file with explicit file list

- **Given** a `design.md` containing a section with file paths in
  backtick-quoted format (e.g., `` `zsiga/pipeline/dependency.py` ``)
- **When** the file is parsed
- **Then** all backtick-quoted paths ending in `.py` or `.md` SHALL be
  extracted into the `target_files` set

#### Scenario: Design file with no file references

- **Given** a `design.md` that does not contain any backtick-quoted file paths
- **When** the file is parsed
- **Then** the `target_files` set SHALL be empty

#### Scenario: Deduplicated and normalized file paths

- **Given** a `design.md` that mentions the same file path multiple times
- **When** the file is parsed
- **Then** the `target_files` set SHALL contain each unique path exactly once
