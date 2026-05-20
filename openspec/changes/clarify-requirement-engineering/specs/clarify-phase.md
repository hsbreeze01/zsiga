# Delta Spec: CLARIFY Phase (Replaces ENRICH)

## MODIFIED Requirements

### REQ-CL-001: Phase ENRICH SHALL be renamed to CLARIFY

The pipeline phase historically named "ENRICH" SHALL be renamed to "CLARIFY". The Phase enum value
`Phase.ENRICH` SHALL become `Phase.CLARIFY` with value `"clarify"`. All log output, phase labels,
WAL entries, and metrics records SHALL use the name "clarify" instead of "enrich".

The `PipelineConfig` fields `enrich_max_turns`, `enrich_timeout`, `enrich_parallel_explore` SHALL
retain their current names for backward compatibility — the rename is purely a user-facing and
semantic change, not a config schema change.

#### Scenario: Phase enum uses CLARIFY
- **Given** the Phase enum in `zsiga/metrics/types.py`
- **When** the code references the first pipeline phase
- **Then** the enum member SHALL be `CLARIFY = "clarify"` (not `ENRICH = "enrich"`)

#### Scenario: Orchestrator logs use "clarify" label
- **Given** the orchestrator enters the first pipeline phase
- **When** the phase header is printed
- **Then** the output SHALL say `Phase 1/4: CLARIFY {change_name}` (not `ENRICH`)

#### Scenario: WAL records use "clarify" phase name
- **Given** the first pipeline phase completes
- **When** `PhaseWAL.write()` is called
- **Then** the `current_phase` field SHALL be `"clarify"`

#### Scenario: PhaseRecord uses CLARIFY phase
- **Given** the first pipeline phase completes successfully
- **When** a `PhaseRecord` is appended
- **Then** `phase` SHALL be `Phase.CLARIFY`

### REQ-CL-002: CLARIFY phase SHALL output clarify.md instead of design.md + tasks.md

The CLARIFY phase SHALL produce a single structured file `clarify.md` in the change directory,
replacing the previous `design.md` and `tasks.md` outputs. The `specs/` directory generation
remains unchanged.

The orchestrator condition for skipping the CLARIFY phase SHALL check for the presence of
`specs/` AND `clarify.md`, not the previous `specs/` AND `design.md` AND `tasks.md`.

#### Scenario: CLARIFY phase generates clarify.md
- **Given** a proposal enters the CLARIFY phase without pre-existing artifacts
- **When** the phase completes successfully
- **Then** the change directory SHALL contain `specs/` directory (unchanged) and `clarify.md`
- **And** the change directory SHALL NOT require `design.md` or `tasks.md`

#### Scenario: Skip CLARIFY when artifacts already exist
- **Given** a change directory already contains `specs/` with spec files AND `clarify.md`
- **When** the orchestrator checks whether to run CLARIFY
- **Then** the CLARIFY phase SHALL be skipped

#### Scenario: FIX intent skips CLARIFY (unchanged)
- **Given** the intent classification returns `IntentType.FIX`
- **When** the orchestrator processes the change
- **Then** the CLARIFY phase SHALL be skipped (same as current ENRICH skip behavior)

### REQ-CL-003: CLARIFY phase SHALL be backward compatible with legacy design.md + tasks.md

The scanner and orchestrator SHALL recognize change directories that contain the legacy
combination of `design.md` + `tasks.md` as "already enriched", in addition to the new
`clarify.md` format. This ensures archived changes and in-flight changes are not broken.

#### Scenario: Legacy change with design.md + tasks.md is recognized
- **Given** a change directory contains `specs/`, `design.md`, and `tasks.md` (but no `clarify.md`)
- **When** the scanner evaluates the change
- **Then** the change SHALL be treated as already clarified (skip CLARIFY phase)

#### Scenario: New change with clarify.md is recognized
- **Given** a change directory contains `specs/` and `clarify.md`
- **When** the scanner evaluates the change
- **Then** the change SHALL be treated as already clarified (skip CLARIFY phase)
