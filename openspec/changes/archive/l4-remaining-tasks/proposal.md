# Proposal: l4-remaining-tasks

## Problem

L4 Multi-Project Orchestrator 里程碑还需要 3 个 capability task：
1. Todo 驱动编排 — 缺 dashboard todo progress card
2. 垂直切片实施 — 缺 implementer.py 中的 vertical slice prompt
3. 领域术语缓存 — 缺 pipeline/glossary.py 和 memory/glossary/

## Scope

- **zsiga 自身项目**（self-modify）
- 修改 `zsiga/metrics/dashboard.py`（todo 卡片）
- 修改 `zsiga/pipeline/implementer.py`（vertical slice prompt）
- 新建 `zsiga/pipeline/glossary.py`（术语提取）
- 新建 `zsiga/memory/glossary/` 目录

## Approach

### 1. Dashboard Todo Progress Card

在 `dashboard.py` 的 `_render()` 中添加一个新 section：
- 从 `data/todo_state.json`（如果存在）读取 todo 列表
- 渲染为进度卡片：显示 pending/in_progress/completed 计数和每个 todo 的状态
- 放在 "Resource Usage" section 之后

### 2. Vertical Slice Prompt in Implementer

在 `implementer.py` 中修改 system prompt，加入 vertical slice 策略：
- 每次只修改 1-2 个文件
- 按 task 顺序逐个执行（read → edit → lint → next）
- 反对一次性修改 4-5 个文件
- 在 prompt 中明确说明这一策略

### 3. Domain Glossary

新建 `pipeline/glossary.py`：
- `extract_glossary(target_path, transport)` — 扫描项目的 routes、models、services 提取术语
- `save_glossary(project_name, terms)` — 保存到 `memory/glossary/{project}.json`
- `load_glossary(project_name)` — 加载已缓存术语表
- `inject_glossary_to_context(glossary, context)` — 将术语注入到 project_context

新建 `memory/glossary/` 目录（放入一个 `.gitkeep`）。

## Success Criteria

1. dashboard.html 中包含 todo progress section（或 todo_state.json 不存在时优雅降级）
2. implementer.py 的 prompt 中包含 vertical slice 策略指导
3. pipeline/glossary.py 可 import，有 extract/save/load/inject 四个函数
4. memory/glossary/ 目录存在
5. L4 capability tasks 验证器识别所有 deliverable
