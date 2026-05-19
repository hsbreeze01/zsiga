# Delta Spec: Change Dependency Graph

## ADDED Requirements

### Requirement: Dependency Graph Construction

The system SHALL build a directed acyclic graph (DAG) representing dependencies between openspec changes.

#### Scenario: Build graph from change list with file-level overlaps
- Given a list of ChangeInfo objects where change-A targets `zsiga/pipeline/utils.py` and `zsiga/pipeline/diagnoser.py`, and change-B targets `zsiga/pipeline/utils.py` and `tests/test_foo.py`
- When the dependency graph is constructed
- Then an edge SHALL exist from change-A to change-B (and vice versa) labeled as a file-overlap conflict
- And the graph SHALL contain exactly 2 nodes and 1 edge

#### Scenario: Build graph with no overlaps yields isolated nodes
- Given a list of 3 ChangeInfo objects with mutually exclusive target files
- When the dependency graph is constructed
- Then the graph SHALL contain 3 nodes and 0 edges

#### Scenario: Graph rejects cycles and reports circular dependency
- Given explicit dependency declarations where change-A depends on change-B and change-B depends on change-A
- When the dependency graph is constructed
- Then the system SHALL raise a ValueError indicating a circular dependency was detected

---

### Requirement: Explicit Change Dependencies

The system SHALL parse explicit dependency declarations from change metadata files (tasks.md), in addition to file-level overlap detection.

#### Scenario: Parse `depends-on:` declarations from tasks.md
- Given a tasks.md containing the line `<!-- depends-on: add-user-auth, refactor-database -->`
- When change dependencies are extracted
- Then the system SHALL return `["add-user-auth", "refactor-database"]` as declared dependencies

#### Scenario: Change with no depends-on declarations returns empty list
- Given a tasks.md with no `<!-- depends-on:` markers
- When change dependencies are extracted
- Then the system SHALL return an empty list

---

### Requirement: Conflict Severity Classification

The system SHALL classify conflict severity between change pairs.

#### Scenario: Two changes sharing a .py file yields HIGH severity
- Given change-A and change-B both target `zsiga/pipeline/utils.py`
- When conflict severity is computed
- Then the severity SHALL be "HIGH"

#### Scenario: Two changes sharing a .md file yields LOW severity
- Given change-A targets `README.md` and change-B also targets `README.md`
- When conflict severity is computed
- Then the severity SHALL be "LOW"

#### Scenario: Changes with no shared files yields no conflict
- Given change-A targets `a.py` and change-B targets `b.py`
- When conflict severity is computed
- Then no conflict entry SHALL be produced

---

### Requirement: Topological Execution Order

The system SHALL compute a safe execution order using topological sort on the dependency graph, respecting both explicit dependencies and file-overlap ordering.

#### Scenario: Explicit dependencies respected in order
- Given change-A declares depends-on change-B
- When execution order is computed
- Then change-B SHALL appear before change-A in the result

#### Scenario: File-overlap changes ordered by target file count
- Given change-A targets 3 files and change-B targets 1 file, and they share one file
- When execution order is computed
- Then change-B (fewer targets) SHALL appear before change-A

#### Scenario: Independent changes can execute in any order
- Given 3 changes with no overlaps and no explicit dependencies
- When execution order is computed
- Then all 3 changes SHALL appear in the result in a deterministic (lexicographic) order

---

### Requirement: Conflict Report Generation

The system SHALL produce a human-readable conflict report summarizing all detected conflicts and the suggested execution order.

#### Scenario: Report lists all conflict pairs with severity
- Given 4 changes where change-A overlaps change-B on `utils.py` and change-C overlaps change-D on `README.md`
- When a conflict report is generated
- Then the report SHALL list change-A and change-B as HIGH conflict on `utils.py`
- And the report SHALL list change-C and change-D as LOW conflict on `README.md`
- And the report SHALL include the suggested execution order

#### Scenario: No conflicts yields clean report
- Given 2 changes with no overlaps and no explicit dependencies
- When a conflict report is generated
- Then the report SHALL state that no conflicts were detected
- And the report SHALL include the execution order
