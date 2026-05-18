# Design: L4 Remaining — Dashboard Todo Card, Implementer Vertical Slice, Glossary Cache

## Architecture Decisions

### 1. Dashboard Todo Card
- **Approach**: Add `_todo_section()` function to `metrics/dashboard.py` that reads persisted todo JSON files from `data/todos/` and renders them as milestone-style cards
- **Rationale**: The dashboard already uses static HTML generation via `_render()`. Adding a new section follows the existing pattern (like `_journal_section()`). No new CSS needed — reuse `.milestone`, `.criterion`, `.progress` classes
- **Data source**: `zsiga/agent/todo.py` already persists to JSON. The dashboard just needs to scan `data/todos/*.json` (the convention path used by TodoList)
- **Placement**: Todo section goes between the "Evolution Roadmap" and "Growth Journal" sections

### 2. Implementer Vertical Slice Prompt
- **Approach**: Modify `IMPLEMENTER_SYSTEM` in `pipeline/implementer.py` to add explicit vertical slice instructions
- **Rationale**: The current prompt already says "按 tasks.md 顺序执行", but doesn't enforce file-per-task limits. Adding a "## Vertical Slice Rules" section to the system prompt is the lightest change
- **No code logic change**: The enforcement is prompt-based (the LLM follows instructions). We don't add Python enforcement code because the agent loop is tool-based and the LLM decides which tools to call

### 3. Glossary Cache
- **Approach**: New module `pipeline/glossary.py` with functions `extract_glossary()`, `load_glossary()`, integrated into `project_context.py`
- **Storage**: `memory/glossary/<project_name>.json` — simple JSON files, one per project
- **Cache TTL**: 24 hours — projects don't change structure that often
- **Extraction strategy**: Use `ast_search` tool concept at Python level — scan files with regex patterns for class/function/route/config definitions. Keep it simple (regex over AST) because the glossary is approximate, not precise
- **Integration point**: `build_project_context()` in `project_context.py` calls `load_glossary()` and appends result as a new section

## Data Flow

```
Todo Card:
  data/todos/*.json → _load_todos() → _todo_section() → HTML in dashboard

Vertical Slice:
  IMPLEMENTER_SYSTEM prompt → LLM reads tasks.md → executes 1 task at a time

Glossary Cache:
  First time: target project files → extract_glossary() → memory/glossary/<name>.json
  Subsequent: memory/glossary/<name>.json → load_glossary() → project_context.py appends section
```

## Files to Create/Modify

### New Files
- `zsiga/pipeline/glossary.py` — Glossary extraction and caching
- `zsiga/memory/glossary/` — Directory for cached glossary JSON files

### Modified Files
- `zsiga/metrics/dashboard.py` — Add `_todo_section()` and `_load_todos()`, integrate into `_render()`
- `zsiga/pipeline/implementer.py` — Add vertical slice rules to `IMPLEMENTER_SYSTEM`
- `zsiga/pipeline/project_context.py` — Import and integrate glossary into `build_project_context()`

### Test Files
- `tests/test_todo_card.py` — Dashboard todo section rendering tests
- `tests/test_glossary.py` — Glossary extraction, caching, and loading tests
