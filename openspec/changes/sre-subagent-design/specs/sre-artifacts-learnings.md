# Spec: SRE Artifacts and Learnings

## ADDED Requirements

### Requirement: Execution Report Format

The `execution_report.md` produced by the REPORT phase SHALL follow a structured markdown format. It SHALL contain the following sections in order:

1. `# SRE Execution Report` — title
2. `## Intent` — the original intent description
3. `## Timeline` — a table with columns Phase / Status / Duration
4. `## Commands` — a table with columns Command / Exit Code / Output (truncated)
5. `## Verification` — comparison of pre/post state with pass/fail result
6. `## Summary` — one-paragraph human-readable summary

#### Scenario: Report contains all required sections

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::generate_report_content
- **Given** completed pipeline results with intent, phases, commands, and verification data
- **When** `generate_report_content(results)` is called
- **Then** the output string SHALL contain `# SRE Execution Report`
- **And** SHALL contain `## Intent`
- **And** SHALL contain `## Timeline`
- **And** SHALL contain `## Commands`
- **And** SHALL contain `## Verification`
- **And** SHALL contain `## Summary`

#### Scenario: Report commands table includes all executed commands

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::generate_report_content
- **Given** pipeline results containing 2 executed commands
- **When** `generate_report_content(results)` is called
- **Then** the `## Commands` section SHALL list both commands with their exit codes

### Requirement: SRE Learnings Injection

After a completed SRE pipeline run (success or failure), the system SHALL record an operational lesson to `learnings.jsonl` via `record_lesson()`. The lesson SHALL have:
- `title`: `"SRE: {intent_summary}"` where `intent_summary` is a truncated version of the verbalization
- `context`: the phases completed and commands executed
- `takeaway`: a description of what happened and any lessons
- `pattern_key`: `"sre.success"` for successful runs, `"sre.failure"` for failed runs
- `source`: `"sre_pipeline"`

#### Scenario: Successful SRE run records success lesson

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::record_sre_lesson
- **Given** a successful SRE pipeline result with `success=True`
- **When** `record_sre_lesson(result)` is called
- **Then** `record_lesson()` SHALL be called with `pattern_key="sre.success"` and `source="sre_pipeline"`

#### Scenario: Failed SRE run records failure lesson

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::record_sre_lesson
- **Given** a failed SRE pipeline result with `success=False`
- **When** `record_sre_lesson(result)` is called
- **Then** `record_lesson()` SHALL be called with `pattern_key="sre.failure"` and `source="sre_pipeline"`

### Requirement: No Git Operations in SRE Pipeline

The SRE pipeline SHALL NOT call any git operations: no `git add`, `git commit`, `git tag`, `git checkout`, `git push`, `git merge`, or `git branch`. The SRE pipeline is purely operational and produces no code changes.

#### Scenario: SRE pipeline does not create git commits

- **testable**: false

- **Given** a completed SRE pipeline run
- **When** the pipeline finishes
- **Then** the git log SHALL show no new commits attributable to the SRE pipeline

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
