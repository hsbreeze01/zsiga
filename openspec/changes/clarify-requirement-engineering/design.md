# Design: CLARIFY Phase — Requirement Engineering Renovation

## Architecture Decision

Replace the ENRICH phase with CLARIFY: instead of generating `design.md` + `tasks.md`,
the new phase produces a single `clarify.md` structured as a **requirements contract**
with four dimensions (decomposition, boundary, goal, constraint). The `specs/` directory
generation remains unchanged.

**Key principle**: `clarify.md` is consumed by IMPLEMENT, VERIFY, and DELIVER phases
as the single source of truth for "what to build" and "how to validate it".

**Backward compatibility**: Legacy changes with `design.md` + `tasks.md` continue to work
throughout the pipeline. The scanner, implementer, and verifier all support both formats
with a clear precedence: `clarify.md` takes priority when present.

## Data Flow

```
PROPOSAL.md
  │
  ▼
CLARIFY phase (was ENRICH):
  │  Input:  proposal.md + project_context + optional explore results
  │  Output: specs/*.md + clarify.md
  │
  ├─ specs/ directory (unchanged — behavioral delta specs)
  │
  └─ clarify.md (NEW — replaces design.md + tasks.md):
       ├── ## 需求拆解
       │     ├── 原始需求
       │     └── 拆解后的子任务 (numbered, each with complexity + token estimate)
       ├── ## 边界
       │     ├── IN scope
       │     ├── OUT of scope
       │     └── 依赖的外部条件
       ├── ## 目标
       │     ├── 成功标准
       │     └── 验收方式
       └── ## 约束
             ├── 不能修改的文件
             ├── 项目部署分支
             ├── 已知风险
             └── 预估 token 消耗
  │
  ▼
IMPLEMENT phase:
  │  Reads: specs/ + clarify.md (or specs/ + design.md + tasks.md for legacy)
  │  Tasks from clarify.md ## 需求拆解 → - [ ] checklist format
  │  Boundaries from clarify.md ## 边界 → file scope restrictions
  │  Constraints from clarify.md ## 约束 → protected files, risk awareness
  │
  ▼
VERIFY phase:
  │  Reads: specs/ + clarify.md (or legacy)
  │  Success criteria from clarify.md ## 目标 → verification checklist
  │
  ▼
DELIVER phase: (unchanged)
```

## Historical Token Estimation

The `## 约束 > 预估 token 消耗` field uses historical data from `zsiga.db` metrics:

1. The enricher calls a new function `estimate_token_budget(change_name: str, db_path: str) -> dict`
2. This function queries the `phase_records` table for similar changes (by keyword matching on
   change_name or by averaging recent IMPLEMENT phase token usage)
3. Returns `{"estimated_prompt": int, "estimated_completion": int, "source": "historical" | "none"}`
4. If no history exists, returns `{"source": "none"}` and clarify.md states "无历史参考"

The estimation function is pure (no side effects) and lives in `zsiga/pipeline/enricher.py`
alongside the existing `enrich()` function.

## Clarify.md Format Template

The system prompt instructs the LLM to produce `clarify.md` in this exact structure:

```markdown
## 需求拆解

### 原始需求
[从 proposal.md 提取的核心需求描述]

### 拆解后的子任务
- [ ] 1. <description> (预估复杂度：低/中/高, 预估 token：~NNNN / 无历史参考)
- [ ] 2. ...

## 边界

### IN scope
- <item 1>
- <item 2>

### OUT of scope
- <item 1>

### 依赖的外部条件
- <item 1>

## 目标

### 成功标准
1. <criterion 1>
2. <criterion 2>

### 验收方式
- <method 1: e.g., pytest tests/test_xxx.py passes>
- <method 2: e.g., manual curl verification>

## 约束

### 不能修改的文件
- <file 1>

### 项目部署分支
<branch_name>

### 已知风险
- <risk 1: derived from pattern_miner>

### 预估 token 消耗
- prompt: ~NNNN
- completion: ~NNNN
- 数据来源: historical / 无历史参考
```

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `zsiga/metrics/types.py` | MODIFY | `Phase.ENRICH` → `Phase.CLARIFY` with value `"clarify"` |
| `zsiga/pipeline/enricher.py` | MODIFY | New system prompt for four-dimension output; `enrich()` generates `clarify.md`; add `estimate_token_budget()`; add `_validate_clarify()` |
| `zsiga/pipeline/orchestrator.py` | MODIFY | Phase label "enrich" → "clarify"; skip condition checks `has_clarify`; WAL phase name |
| `zsiga/intake/scanner.py` | MODIFY | Detect `clarify.md`; add `has_clarify` field; update `is_enriched()` for dual format |
| `zsiga/pipeline/implementer.py` | MODIFY | Read `clarify.md` when present; parse four sections; fallback to legacy |
| `zsiga/pipeline/verifier.py` | MODIFY | Read `clarify.md` when present; use `## 目标` success criteria; fallback to legacy |

## Config

No config schema changes. The existing `PipelineConfig.enrich_max_turns`, `enrich_timeout`,
`enrich_parallel_explore` fields retain their names (backward compatible). The code internally
refers to the phase as CLARIFY but reads from the same config fields.

## Validation Strategy

1. Unit tests for `estimate_token_budget()` — mock DB, test with/without historical data
2. Unit tests for `_validate_clarify()` — test with valid clarify.md, missing sections, empty file
3. Unit tests for scanner `is_enriched()` — test new format, legacy format, partial artifacts
4. Unit tests for implementer/verifier `clarify.md` reading — test new format, legacy fallback
5. Integration: existing orchestrator test patterns adapted for CLARIFY phase name
6. `ruff check zsiga/` — zero errors
7. `pytest tests/` — all pass
