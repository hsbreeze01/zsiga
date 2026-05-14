# Design: Fix Self Lint Issues

## Architecture Decision

This is a **pure cleanup change** — no new modules, no new functions, no API changes. The approach is:

1. Run `diagnostics` (ruff check) on each file under `zsiga/`
2. For each reported issue, use `goto_definition` / `find_references` to confirm the symbol is genuinely unused
3. Apply the minimal fix (remove import, convert f-string, remove variable) and re-verify with `diagnostics`

No architectural changes are needed. The lint fixes are localised to individual lines.

## Files to Modify

| File | Issue Types | Expected Changes |
|------|-------------|-----------------|
| `zsiga/agent/loop.py` | F401 (unused imports: `asyncio`, `subprocess`, `Path`), F841 (unused vars: `llm_ms`, `result_lines`) | Remove unused imports; remove or consume unused variables |
| `zsiga/agent/tools.py` | F401 (unused imports: `json`, `os`) | Remove unused import lines |
| `zsiga/__main__.py` | F541 (f-strings without placeholders in print statements) | Convert f-strings to plain strings; F401 (`threading`) remove unused import |
| `zsiga/agent/compaction.py` | F841 (unused variable: `content`) | Remove unused assignment |
| `zsiga/metrics/collector.py` | F401 (unused imports) | Remove unused imports |
| `zsiga/metrics/dashboard.py` | F401 (unused imports) | Remove unused imports |
| Other `zsiga/` files as discovered | F401 / F541 / F841 | Fix per-type |

## Data Flow

```
diagnostics(file) → filter F401/F541/F841 → find_references(symbol) → apply fix → diagnostics(file) confirm 0
```

No data flow changes. No database changes. No config changes.

## Verification Strategy

1. `ruff check zsiga/` — MUST report 0 errors after all fixes
2. `pytest tests/` — MUST pass with no regressions
