# Tasks: CLARIFY Phase — Requirement Engineering Renovation

## 1. Core Type & Enum Change

- [x] **1.1** Rename `Phase.ENRICH` to `Phase.CLARIFY` in `zsiga/metrics/types.py`
  - Change `ENRICH = "enrich"` to `CLARIFY = "clarify"`
  - Update all references across the codebase (orchestrator, phase_wal, metrics)
  - Files: `zsiga/metrics/types.py`

## 2. Enricher → Clarifier (Core Logic)

- [x] **2.1** Rewrite enricher system prompt and output logic for four-dimension clarify.md
  - Replace `ENRICHER_SYSTEM` prompt to instruct LLM to output `clarify.md` with four sections (需求拆解, 边界, 目标, 约束) instead of `design.md` + `tasks.md`
  - Change `enrich()` function: after agent run, validate `clarify.md` exists (not design.md/tasks.md)
  - Add `_validate_clarify()` that checks for all four `##` headings
  - Update user prompt to instruct `write_file` for `{change_dir}/clarify.md`
  - Remove retry logic for missing `design.md`/`tasks.md`; add retry for missing `clarify.md` sections
  - Files: `zsiga/pipeline/enricher.py`

- [x] **2.2** Add historical token estimation function `estimate_token_budget()`
  - Query `zsiga.db` metrics for recent IMPLEMENT phase records (prompt_tokens, completion_tokens)
  - Return average token usage as estimate dict, or `{"source": "none"}` if no history
  - Inject estimate into enricher user prompt so LLM can populate `## 约束 > 预估 token 消耗`
  - Files: `zsiga/pipeline/enricher.py`

## 3. Scanner Integration

- [x] **3.1** Update `DirectoryScanner` to detect `clarify.md` and support dual format
  - Add `has_clarify` field detection (case-insensitive lookup like existing design.md/tasks.md)
  - Update `is_enriched()`: return True if `(has_specs and has_clarify)` OR `(has_specs and has_design and has_tasks)`
  - Files: `zsiga/intake/scanner.py`

## 4. Downstream Phase Integration

- [ ] **4.1** Update implementer to read `clarify.md` with legacy fallback
  - In `implement()`: if `clarify.md` exists, read it and parse four sections into the user prompt
  - Build task list from `## 需求拆解 > 拆解后的子任务` section
  - Inject boundary constraints from `## 边界` into system prompt
  - Inject risk warnings from `## 约束 > 已知风险` into system prompt
  - If no `clarify.md`, fall back to reading `design.md` + `tasks.md` (existing logic)
  - Files: `zsiga/pipeline/implementer.py`

- [ ] **4.2** Update verifier to read `clarify.md` with legacy fallback
  - In `verify()`: if `clarify.md` exists, read it and include success criteria in prompt
  - Add `## 目标` section to user prompt so verifier checks against defined success criteria
  - If no `clarify.md`, fall back to reading `design.md` + `tasks.md` (existing logic)
  - Files: `zsiga/pipeline/verifier.py`

## 5. Orchestrator Updates

- [ ] **5.1** Update orchestrator phase naming and skip condition for CLARIFY
  - Rename all "Phase 1/4: ENRICH" prints to "Phase 1/4: CLARIFY"
  - Update skip condition: `not (prop["has_specs"] and (prop.get("has_clarify") or (prop["has_design"] and prop["has_tasks"])))`
  - Update `self.agent.set_phase("enrich")` to `self.agent.set_phase("clarify")`
  - Update WAL write phase name from `"enrich"` to `"clarify"`
  - Update PhaseRecord to use `Phase.CLARIFY`
  - Files: `zsiga/pipeline/orchestrator.py`

## 6. Tests

- [ ] **6.1** Add tests for CLARIFY phase logic (scanner, enricher validation, implementer/verifier reading)
  - Test `DirectoryScanner.is_enriched()` with: clarify.md present, legacy format, partial artifacts
  - Test `_validate_clarify()` with: valid four-section file, missing section, empty file
  - Test `estimate_token_budget()` with: mock DB with history, empty DB
  - Test implementer `_read_clarify()` parsing of four sections
  - Test verifier includes clarify.md success criteria in prompt
  - Files: `tests/test_clarify.py` (NEW)
