# Tasks: Session Summary Exporter

## 1. Core Export Logic

- [x] **1.1** Add `export_session` function to `zsiga/memory/journal.py`
  - Add `_SESSIONS_DIR` constant, `export_session(change_name, db_path=None) -> str | None` function
  - Find matching change from DB via `load_all_changes`, collect lessons from `memory/learnings.jsonl` by matching change name in lesson title
  - Compute aggregated metrics from phase records (total LLM/tool calls, tokens, runtime)
  - Write structured JSON to `memory/sessions/{YYYYMMDD-HHmmss}-{change_name}.json`
  - Auto-create `memory/sessions/` directory
  - Return file path on success, `None` if change not found

- [x] **1.2** Add `load_sessions` function to `zsiga/memory/journal.py`
  - `load_sessions(limit: int = 0) -> list[dict]` reads all `*.json` from `memory/sessions/`
  - Sort by filename (chronological), apply limit (return last N), return list of dicts oldest-first
  - Return `[]` if directory missing or empty

## 2. Pipeline Integration

- [x] **2.1** Integrate `export_session` into `zsiga/pipeline/orchestrator.py`
  - Import `export_session` from `..memory.journal`
  - Call `export_session(change_name)` in `_process_change()` after `record_change(rec)` in the `finally` block

## 3. Tests

- [x] **3.1** Add unit tests in `tests/test_session_export.py`
  - Test `export_session` writes correct JSON structure for a successful change
  - Test `export_session` returns `None` for non-existent change name
  - Test `load_sessions` returns recent sessions in correct order
  - Test `load_sessions` returns empty list when no sessions directory
  - Test auto-creation of `memory/sessions/` directory
  - Use temp directories and in-memory DB for isolation
