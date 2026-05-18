# Tasks

## 1. Core Data Structures & Clustering
- [x] 1.1 Add `skills/__init__.py` (empty package) and `skills/skill_evolver.py` with `ClusterInfo` dataclass and `_cluster_patterns()` function that groups `Pattern` objects by shared dot-prefix (first 2 segments) and returns `dict[str, ClusterInfo]`

## 2. Skill File Generation
- [x] 2.1 Implement `_generate_skill_markdown(cluster)` that produces the full markdown content (YAML frontmatter + pattern table + deduplicated guidelines) for a single cluster
- [x] 2.2 Implement `_derive_filename(prefix)` for the `pipeline.fail` → `pipeline-fail.md` naming convention

## 3. Evolution Entry Point
- [x] 3.1 Implement `evolve_skills(min_cluster_occurrences, learnings_path, skills_dir)` that orchestrates: mine patterns → cluster → generate/update qualifying skill files → prune stale auto-generated files → return list of written paths

## 4. Idempotent Update & Protection
- [x] 4.1 Implement `_is_auto_generated(path)` check (parse YAML frontmatter for `auto_generated: true`) and `_prune_stale_skills()` that removes auto-generated skill files whose cluster no longer qualifies

## 5. Tests
- [x] 5.1 Add `tests/test_skill_evolver.py` covering: clustering logic, skill generation format, filename derivation, idempotent re-generation, hand-written skill protection, stale skill pruning, empty/minimal learnings edge cases
