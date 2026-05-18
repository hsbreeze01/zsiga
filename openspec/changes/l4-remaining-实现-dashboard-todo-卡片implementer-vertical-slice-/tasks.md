# Tasks: L4 Remaining

## Group 1: Dashboard Todo Card

- [ ] 1.1 添加 `_load_todos()` 数据函数到 `zsiga/metrics/dashboard.py` — 扫描 `data/todos/*.json`，按 mtime 排序取最近 5 个，返回 `[{"name": ..., "summary": ..., "items": [...]}]`
- [ ] 1.2 添加 `_todo_section()` 渲染函数并集成到 `_render()` — 使用已有 `.milestone`/`.criterion`/`.progress` CSS 样式渲染 todo 卡片，插到 Evolution Roadmap 和 Growth Journal 之间；添加对应测试 `tests/test_todo_card.py`

## Group 2: Implementer Vertical Slice Prompt

- [ ] 2.1 修改 `IMPLEMENTER_SYSTEM` 添加垂直切片规则 — 在 `zsiga/pipeline/implementer.py` 的 `IMPLEMENTER_SYSTEM` 末尾追加 `## Vertical Slice Rules` 段，规定每次只取 1 个 task、最多编辑 2 个文件、每 task 完成后立即跑 lint 和相关测试

## Group 3: Glossary Cache

- [ ] 3.1 创建 `zsiga/pipeline/glossary.py` — 实现 `Glossary` dataclass、`extract_glossary(target_path, transport)` 扫描项目提取类名/函数名/路由/配置键、`load_glossary(project_name, target_path, transport)` 带 24h TTL 缓存、持久化到 `memory/glossary/<name>.json`
- [ ] 3.2 集成 glossary 到 `zsiga/pipeline/project_context.py` — 在 `build_project_context()` 末尾追加 `_glossary_section()` 调用，将缓存的术语表作为 `## Domain Glossary` section 注入项目上下文；添加对应测试 `tests/test_glossary.py`
