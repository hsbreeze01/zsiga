# Delta Spec: pipeline/dependency.py — ChangeGraph

## ADDED Requirements

### Requirement: ChangeGraph Constructor
The system SHALL provide a `ChangeGraph` class whose constructor accepts a single argument: the filesystem path to an openspec directory.

#### Scenario: Constructing a ChangeGraph with a valid directory
- Given an openspec directory path exists on the filesystem
- When `ChangeGraph(openspec_dir)` is called
- Then a new `ChangeGraph` instance is returned with an empty internal change registry

#### Scenario: Constructing with a non-existent directory
- Given an openspec directory path does NOT exist on the filesystem
- When `ChangeGraph(openspec_dir)` is called
- Then a `FileNotFoundError` MUST be raised

---

### Requirement: add_change — Register a Change by Reading proposal.md
The `ChangeGraph` class SHALL provide an `add_change(change_name: str)` method that reads the `proposal.md` file under `openspec_dir/changes/<change_name>/proposal.md`, extracts the **target file list** from it, and registers the change internally.

#### Scenario: Adding a change with a valid proposal.md
- Given an openspec directory containing `changes/my-feature/proposal.md`
- And the proposal.md contains a list of target files (e.g. `## Target Files` section or similar structured content)
- When `add_change("my-feature")` is called
- Then the change named `"my-feature"` is registered with its extracted target file list

#### Scenario: Adding a change with no proposal.md
- Given an openspec directory where `changes/missing-change/proposal.md` does not exist
- When `add_change("missing-change")` is called
- Then a `FileNotFoundError` MUST be raised

#### Scenario: Adding a duplicate change name
- Given a change named `"my-feature"` has already been added
- When `add_change("my-feature")` is called again
- Then a `ValueError` MUST be raised

---

### Requirement: check_conflicts — Detect Overlapping File Targets
The `ChangeGraph` class SHALL provide a `check_conflicts() -> list[tuple[str, str, list[str]]]` method that returns a list of conflict records. Each record is a tuple of `(change_a, change_b, overlapping_files)` where `change_a` and `change_b` are distinct change names that share at least one target file.

#### Scenario: No conflicts
- Given two changes have been added with completely disjoint target file lists
- When `check_conflicts()` is called
- Then an empty list is returned

#### Scenario: Two changes share target files
- Given change `"alpha"` targets `["src/a.py", "src/b.py"]`
- And change `"beta"` targets `["src/b.py", "src/c.py"]`
- When `check_conflicts()` is called
- Then the result SHALL contain a tuple `("alpha", "beta", ["src/b.py"])`

#### Scenario: Multiple pairs of conflicts
- Given three changes where `"alpha"` and `"beta"` overlap, and `"beta"` and `"gamma"` overlap on different files
- When `check_conflicts()` is called
- Then the result SHALL contain one conflict record for each overlapping pair

---

### Requirement: execution_order — Topological Sort of Changes
The `ChangeGraph` class SHALL provide an `execution_order() -> list[str]` method that returns change names in a valid topological order. Two changes have a dependency edge from A to B when they share at least one target file (i.e., they conflict) and A's name is lexicographically before B's name (to break ties deterministically).

#### Scenario: Single change
- Given only one change `"solo"` has been added
- When `execution_order()` is called
- Then `["solo"]` is returned

#### Scenario: Independent changes
- Given two changes with disjoint target files
- When `execution_order()` is called
- Then both names are returned in lexicographic order

#### Scenario: Dependent changes produce a valid order
- Given changes `"alpha"` and `"beta"` share target files
- When `execution_order()` is called
- Then the result is a topologically sorted list where `"alpha"` appears before `"beta"` (or vice versa), respecting the dependency edge direction
- And the list MUST contain all registered change names exactly once

#### Scenario: Cycle detection
- Given the internal dependency graph contains a cycle
- When `execution_order()` is called
- Then a `CycleError` MUST be raised
