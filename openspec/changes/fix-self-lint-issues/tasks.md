# Tasks: Fix Self Lint Issues

## 1. Agent & Loop Module Cleanup

- [ ] **1.1** Fix `zsiga/agent/loop.py` — remove unused imports (`asyncio`, `subprocess`, `Path`), remove unused variables (`llm_ms`, `result_lines`). Use `find_references` to confirm each before removal.
- [ ] **1.2** Fix `zsiga/agent/tools.py` — remove unused imports (`json`, `os`). Use `find_references` to confirm.

## 2. Main Entry Point Cleanup

- [ ] **2.1** Fix `zsiga/__main__.py` — remove unused import (`threading`), convert f-strings without placeholders to plain strings in print statements.

## 3. Compaction & Metrics Cleanup

- [ ] **3.1** Fix `zsiga/agent/compaction.py` — remove unused variable (`content`).
- [ ] **3.2** Fix `zsiga/metrics/collector.py` and `zsiga/metrics/dashboard.py` — remove unused imports found by diagnostics.

## 4. Remaining Files & Final Verification

- [ ] **4.1** Scan remaining `zsiga/` files with `diagnostics`, fix any additional F401/F541/F841 issues discovered.
- [ ] **4.2** Run `ruff check zsiga/` to confirm zero errors, then run `pytest tests/` to confirm no regressions.
