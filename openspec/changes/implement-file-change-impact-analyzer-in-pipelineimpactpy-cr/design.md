# Design: File Change Impact Analyzer

## Architecture Decision

Create a new module `zsiga/pipeline/impact.py` following the established pipeline patterns (dataclass models, Transport-based file access, utility functions). This module analyzes the blast radius of file changes by building an import graph and classifying risk.

## Data Flow

```
Changed Files (list[str])
        │
        ▼
┌──────────────────────┐
│  Build Import Graph  │  Parse all .py files → extract import edges → adjacency dict
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  Reverse Traversal   │  For each changed file, BFS/DFS on reversed graph
│  → downstream deps   │  → collect all transitive dependents
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  Test Scope Match    │  1. Scan test files for imports of changed modules
│                      │  2. Fallback: naming convention (test_<module>.py)
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  Risk Classification │  Rules: dependent count + test coverage + core-file check
└──────────────────────┘
        │
        ▼
  ImpactReport (dataclass)
```

## Key Design Choices

### 1. Import parsing via `ast` module (stdlib)

Use Python's built-in `ast` to parse each `.py` file and extract `Import` and `ImportFrom` nodes. This avoids external dependencies and handles syntax-edge cases gracefully (skip files that fail to parse).

### 2. Transport-based file discovery

Follow `pipeline/utils.py` and `pipeline/dependency.py` patterns: use `Transport.run_shell` for file listing and reading, enabling both local and SSH target execution.

### 3. Path normalization

All file paths are normalized to **relative paths from project root** (e.g., `zsiga/pipeline/utils.py`). Import references like `from zsiga.pipeline.utils import read_file` are resolved to `zsiga/pipeline/utils.py` by replacing dots with `/` and appending `.py`.

### 4. Core infrastructure files

Files matching `*/transport.py`, `*/config.py`, or `*/pipeline/utils.py` are classified as core infrastructure, triggering automatic `high` risk if changed.

### 5. Data models

```python
@dataclass
class ImpactReport:
    changed_files: list[str]
    downstream: dict[str, list[str]]      # file → its downstream dependents
    test_scope: list[str]                 # test files covering changes
    risk_level: str                       # "low" | "medium" | "high"
    summary: str                          # human-readable description
```

## Files to Add/Modify

| File | Action | Description |
|------|--------|-------------|
| `zsiga/pipeline/impact.py` | **ADD** | New module: import graph builder, downstream resolver, test scope matcher, risk classifier, `analyze_impact` entry point |
| `tests/test_impact.py` | **ADD** | Tests for all impact analysis scenarios |

## Dependencies

- `ast` (stdlib) — import statement extraction
- `os` (stdlib) — path manipulation
- `collections` (stdlib) — `defaultdict` for adjacency list
- `zsiga.transport` — Transport/LocalTransport (existing)
- `zsiga.pipeline.utils` — `read_file`, `file_exists`, `list_files_recursive` (existing)
