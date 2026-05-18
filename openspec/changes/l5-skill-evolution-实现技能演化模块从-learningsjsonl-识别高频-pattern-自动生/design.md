# Design: Skill Evolution Module

## Overview

The skill evolution module (`skills/skill_evolver.py`) reads high-frequency patterns from the existing `pattern_miner.py` infrastructure, clusters them by shared prefix, and generates markdown skill files in the `skills/` directory. Generated files coexist with hand-written skills but are clearly marked via `auto_generated: true` frontmatter.

## Architecture Decisions

### AD1: Reuse `pattern_miner.mine_patterns()` as data source
Rather than re-parsing `learnings.jsonl`, the evolver consumes the `Pattern` objects already produced by `mine_patterns()`. This avoids duplicated parsing logic and ensures severity classification stays consistent.

### AD2: Cluster by first two dot-delimited segments
Pattern keys like `pipeline.fail.implement`, `pipeline.fail.verify` share the prefix `pipeline.fail`. Clustering by the first two segments (or first segment if only one exists) produces meaningful skill categories. This is a simple deterministic rule — no ML needed.

### AD3: Separate module under `skills/` package
The evolver lives at `skills/skill_evolver.py` (new package), distinct from `memory/pattern_miner.py`. Rationale: pattern mining is a memory/cognitive function; skill evolution is a capability-building function. They consume each other through a clean API boundary.

### AD4: YAML frontmatter parity with existing skills
Existing hand-written skills (`enrich.md`, `implement.md`, `safety.md`, `verify.md`) use YAML frontmatter with `name` and `description`. Generated skills add `auto_generated: true` to distinguish them and enable safe overwrite/deletion.

## Data Flow

```
learnings.jsonl
       │
       ▼
pattern_miner.mine_patterns()  →  list[Pattern]
       │
       ▼
skill_evolver._cluster_patterns()  →  dict[str, ClusterInfo]
       │                          (key: cluster prefix, value: aggregated data)
       ▼
skill_evolver._generate_skill_markdown()  →  skill file content (str)
       │
       ▼
skills/<cluster-key>.md  (written to disk)
```

## Key Data Structures

```python
@dataclass
class ClusterInfo:
    prefix: str                    # e.g., "pipeline.fail"
    patterns: list[Pattern]        # member Pattern objects
    total_count: int               # sum of all pattern counts
    all_takeaways: list[str]       # deduplicated takeaways
    severity: Severity             # highest severity among members
```

## File Changes

### New Files
| File | Purpose |
|------|---------|
| `skills/__init__.py` | Package init (empty) |
| `skills/skill_evolver.py` | Core module: clustering, generation, evolution entry point |

### New Test Files
| File | Purpose |
|------|---------|
| `tests/test_skill_evolver.py` | Tests for clustering, generation, update, prune, idempotency |

### Files NOT Modified
| File | Reason |
|------|--------|
| `zsiga/memory/pattern_miner.py` | Consumed as-is, no changes needed |
| `skills/enrich.md`, `skills/implement.md`, etc. | Hand-written skills must not be touched |
| `zsiga/memory/context.py` | Future integration point, out of scope for this change |

## Skill File Format (Generated)

```markdown
---
name: <human-readable name derived from cluster prefix>
description: Auto-generated skill from <N> recurring patterns
auto_generated: true
---

# <Cluster Title>

> Auto-generated from recurring patterns in learnings.jsonl.
> Last updated: <ISO timestamp>

## Patterns Observed

| Pattern | Count | Severity |
|---------|-------|----------|
| pipeline.fail.implement | 6 | high |
| pipeline.fail.verify | 2 | high |

## Guidelines

- <deduplicated takeaway 1>
- <deduplicated takeaway 2>
- ...
```
