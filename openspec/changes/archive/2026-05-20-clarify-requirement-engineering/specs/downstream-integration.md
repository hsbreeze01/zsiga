# Delta Spec: Downstream Phase Integration with clarify.md

## MODIFIED Requirements

### REQ-DI-001: Scanner SHALL detect clarify.md as enriched marker

The `DirectoryScanner` SHALL recognize a change directory as "enriched" (ready for IMPLEMENT)
when it contains either:
- (Legacy) `specs/` AND `design.md` AND `tasks.md`
- (New) `specs/` AND `clarify.md`

The scanner SHALL add a `has_clarify` field to the proposal dict, set to `True` when
`clarify.md` is found (case-insensitive).

#### Scenario: Scanner detects new-format change with clarify.md
- **Given** a change directory contains `proposal.md`, `specs/spec.md`, and `clarify.md`
- **When** `DirectoryScanner.scan()` processes the directory
- **Then** the returned proposal dict SHALL have `has_specs=True`, `has_clarify=True`
- **And** `has_design` and `has_tasks` MAY be `False`

#### Scenario: Scanner detects legacy-format change
- **Given** a change directory contains `proposal.md`, `specs/spec.md`, `design.md`, and `tasks.md`
- **When** `DirectoryScanner.scan()` processes the directory
- **Then** the returned proposal dict SHALL have `has_specs=True`, `has_design=True`, `has_tasks=True`
- **And** `has_clarify` MAY be `False`

#### Scenario: is_enriched returns True for new format
- **Given** a proposal dict with `has_specs=True` and `has_clarify=True`
- **When** `is_enriched()` is called
- **Then** it SHALL return `True`

#### Scenario: is_enriched returns True for legacy format
- **Given** a proposal dict with `has_specs=True`, `has_design=True`, `has_tasks=True`
- **When** `is_enriched()` is called
- **Then** it SHALL return `True`

### REQ-DI-002: IMPLEMENT phase SHALL read clarify.md when available

The implementer SHALL read `clarify.md` when it exists in the change directory. If `clarify.md`
is present, it SHALL be used as the source for task decomposition and boundary constraints.
If `clarify.md` is absent but `design.md` and `tasks.md` are present (legacy), the implementer
SHALL fall back to the old behavior.

The implementer system prompt SHALL be updated to instruct the agent to:
- Read tasks from the `## 需求拆解` section of `clarify.md`
- Respect the `## 边界` section (do not modify OUT of scope items)
- Reference `## 约束` for protected files and risk awareness

#### Scenario: Implementer reads clarify.md for new-format change
- **Given** a change directory contains `clarify.md` and `specs/`
- **When** the implementer loads artifacts
- **Then** it SHALL read `clarify.md` and parse its four sections
- **And** it SHALL NOT require `design.md` or `tasks.md`

#### Scenario: Implementer falls back to legacy format
- **Given** a change directory contains `design.md`, `tasks.md`, and `specs/` but no `clarify.md`
- **When** the implementer loads artifacts
- **Then** it SHALL read `design.md` and `tasks.md` using the existing logic
- **And** behavior SHALL be identical to the current implementation

### REQ-DI-003: VERIFY phase SHALL validate against clarify.md success criteria

The verifier SHALL read `clarify.md` when available and use the `## 目标` section's
success criteria as the basis for its verdict. If `clarify.md` is absent, the verifier
SHALL fall back to reading `design.md` and `tasks.md` (legacy behavior).

#### Scenario: Verifier uses clarify.md success criteria
- **Given** a change directory contains `clarify.md` with `## 目标 > 成功标准` listing 3 criteria
- **When** the VERIFY phase evaluates the implementation
- **Then** the verifier SHALL check each criterion from `clarify.md`
- **And** the `verify.md` output SHALL reference which criteria passed/failed

#### Scenario: Verifier falls back to legacy format
- **Given** a change directory contains `design.md` and `tasks.md` but no `clarify.md`
- **When** the VERIFY phase evaluates the implementation
- **Then** the verifier SHALL use the existing spec/design/tasks comparison logic
- **And** behavior SHALL be identical to the current implementation

### REQ-DI-004: DELIVER phase SHALL include clarify.md in archival

When archiving a completed change, the `archive_change` function needs no modification
(it moves the entire change directory). However, the DELIVER phase commit message format
SHALL remain unchanged.

#### Scenario: clarify.md is archived with the change
- **Given** a change with `clarify.md` completes the DELIVER phase
- **When** `archive_change()` moves the change directory to archive
- **Then** `clarify.md` SHALL be included in the archived directory
