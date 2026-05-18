# Delta Spec: Skill Evolution Module

## ADDED Requirements

### Requirement: Pattern Clustering
The system SHALL cluster mined patterns from `learnings.jsonl` into skill-relevant groups based on shared `pattern_key` prefix (segmented by `.`). Each cluster SHALL aggregate all patterns that share at least the first two dot-delimited segments (e.g., `pipeline.fail.*`, `ops.*`, `tools.*`).

#### Scenario: Cluster pipeline failure patterns
- GIVEN `learnings.jsonl` contains records with `pattern_key` values `pipeline.fail.implement`, `pipeline.fail.verify`, and `pipeline.fail.escalation`
- WHEN pattern clustering is invoked
- THEN all three patterns SHALL be grouped into a single cluster keyed by `pipeline.fail`

#### Scenario: Cluster single-segment keys
- GIVEN `learnings.jsonl` contains records with `pattern_key` `ops.service_management`
- WHEN pattern clustering is invoked
- THEN the pattern SHALL be grouped into cluster `ops`

#### Scenario: Ignore patterns below occurrence threshold
- GIVEN a pattern appears fewer than `min_cluster_occurrences` total times across its records
- WHEN pattern clustering is invoked
- THEN that pattern key SHALL NOT produce a cluster

### Requirement: Skill File Generation
The system SHALL generate a markdown skill file in `skills/` for each qualifying cluster. A cluster qualifies when its total occurrence count across all member patterns reaches or exceeds `min_cluster_occurrences` (default: 3). Each generated file SHALL follow the existing skill format: YAML frontmatter (`name`, `description`, `auto_generated: true`) followed by a markdown body containing pattern summaries and distilled guidelines derived from `takeaway` values.

#### Scenario: Generate skill for high-frequency cluster
- GIVEN cluster `pipeline.fail` has 6 total occurrences across 3 distinct pattern keys
- WHEN skill generation is invoked with `min_cluster_occurrences=3`
- THEN a file `skills/pipeline-fail.md` SHALL be created with frontmatter `auto_generated: true` and body listing each pattern's count, severity, and aggregated takeaways

#### Scenario: Skip cluster below threshold
- GIVEN cluster `pipeline.fail` has 2 total occurrences
- WHEN skill generation is invoked with `min_cluster_occurrences=3`
- THEN no skill file SHALL be generated for that cluster

### Requirement: Skill File Update (Idempotent Re-generation)
When a skill file already exists and `auto_generated: true` is in its frontmatter, the system SHALL overwrite its content with fresh data from `learnings.jsonl`. Skill files without `auto_generated: true` (hand-written skills) SHALL NOT be modified or overwritten.

#### Scenario: Update existing auto-generated skill
- GIVEN `skills/pipeline-fail.md` exists with `auto_generated: true` in frontmatter
- AND cluster `pipeline.fail` now has 8 total occurrences (up from 6)
- WHEN skill evolution is invoked
- THEN the file SHALL be overwritten with updated occurrence counts and takeaways

#### Scenario: Preserve hand-written skills
- GIVEN `skills/implement.md` exists WITHOUT `auto_generated: true` in frontmatter
- WHEN skill evolution is invoked
- THEN `skills/implement.md` SHALL remain unchanged

### Requirement: Skill File Naming Convention
Generated skill file names SHALL be derived from the cluster key by replacing dots with hyphens and appending `.md` (e.g., cluster `pipeline.fail` → `skills/pipeline-fail.md`).

#### Scenario: Derive filename from cluster key
- GIVEN cluster key is `tools.venv_detection`
- WHEN generating the skill file
- THEN the filename SHALL be `skills/tools-venv_detection.md`

### Requirement: Evolve Skills Entry Point
The module SHALL expose a single public function `evolve_skills(min_cluster_occurrences, learnings_path, skills_dir)` that performs the full pipeline: mine patterns → cluster → generate/update skill files. It SHALL return a list of generated/updated skill file paths.

#### Scenario: Full evolution pipeline
- GIVEN `learnings.jsonl` contains sufficient records for clusters `pipeline.fail` and `ops`
- WHEN `evolve_skills()` is called
- THEN the function SHALL return `["skills/pipeline-fail.md", "skills/ops.md"]` (or a subset matching qualifying clusters)
- AND both files SHALL exist on disk with valid content

#### Scenario: No qualifying clusters
- GIVEN `learnings.jsonl` is empty or no cluster meets the threshold
- WHEN `evolve_skills()` is called
- THEN the function SHALL return an empty list and create no files

### Requirement: Prune Stale Auto-Generated Skills
When a previously generated skill file's cluster no longer meets the occurrence threshold (e.g., learnings were cleaned), the system SHALL delete the stale auto-generated skill file.

#### Scenario: Remove stale skill file
- GIVEN `skills/pipeline-fail.md` exists with `auto_generated: true`
- AND cluster `pipeline.fail` has fewer than `min_cluster_occurrences` total occurrences
- WHEN `evolve_skills()` is called
- THEN `skills/pipeline-fail.md` SHALL be deleted
