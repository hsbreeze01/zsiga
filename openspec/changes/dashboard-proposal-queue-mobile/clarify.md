# Clarify: dashboard-proposal-queue-mobile

## 需求拆解

### 原始需求
改造 dashboard 的 Proposal Queue 区域：合并两个重复/失效的 queue 区块为一个完整的 Python 渲染面板（含"当前处理中"和"排队中"两个子区域），删除对不存在的 /api/status.json 的 JS fetch 逻辑，并添加手机端 @media 兼容性适配。

### 拆解后的子任务

- [ ] 1. **Proposal Queue 面板统一渲染** — 在 `zsiga/metrics/dashboard.py` 中删除静态 `{proposal_queue_section}` 占位和空 `<div id="queue-section">`，改为 Python 直接渲染一个完整 queue 面板 HTML。面板包含"当前处理中"和"排队中"两个子区域。读取 `daemon_state.json` 的 `current_change`/`current_phase` 获取当前状态，扫描 `openspec/changes/` 目录获取排队列表，从各 proposal.md 提取首行标题作为摘要。阶段进度条需渲染完整的 8 阶段（CLARIFY→DELIVER），当前阶段高亮、已完成标绿、未到灰色。无 proposal 时显示 Idle / Queue empty 提示。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)

- [ ] 2. **手机端 @media 兼容性改造** — 在 `site/dashboard.html` 的 `<style>` 中添加 `@media (max-width: 768px)` 查询：卡片网格单列、hero 竖排、表格字号缩小、padding/spacing 调整、阶段进度条 `.phase-progress` 横滚。确保 dashboard.html 与 dashboard.py 生成的 HTML 结构一致（若样式内联在 Python 中则同步修改 Python 侧的 `<style>` 块）。 (预估复杂度：低, 预估 token：~2000 / 无历史参考)

- [ ] 3. **清理失效 JS fetch 逻辑** — 删除 dashboard 模板中 `<script>` 内对 `/api/status.json` 的 `fetch()` 调用及 `updateQueueSection` 函数定义，删除 HTML 中 `<div id="queue-section">` 空占位元素。 (预估复杂度：低, 预估 token：~1000 / 无历史参考)

## 边界

### IN scope
- 合并两个 proposal queue 区块为一个 Python 渲染面板
- 从 `daemon_state.json` 读取当前处理状态（current_change, current_phase, heartbeat）
- 扫描 `openspec/changes/` 目录获取待处理 proposal 列表
- 从各 `proposal.md` 提取首行 `#` 标题作为摘要
- 渲染 8 阶段进度条（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER）
- 添加 `@media (max-width: 768px)` 手机端适配样式
- 删除对 `/api/status.json` 的失效 JS fetch 调用和相关函数/HTML

### OUT of scope
- 新增 API 端点（如 /api/status.json）
- 修改 `daemon.py` 或 daemon 主循环逻辑
- 修改 daemon_state.json 的写入格式
- 添加实时 WebSocket/SSE 推送（本次仅 Python 静态渲染）
- 修改 dashboard 的其他区域（milestone、journal 等）
- 添加新的 Python 依赖

### 依赖的外部条件
- `daemon_state.json` 文件格式稳定（包含 `current_change`, `current_phase`, `heartbeat` 字段）
- `openspec/changes/` 目录结构稳定（每个子目录含 `proposal.md`）
- dashboard.html 的 `<style>` 块可被 Python 渲染逻辑引用或内联

## 目标

### 成功标准
1. Dashboard 页面只存在一个 Proposal Queue 面板，包含"当前处理中"和"排队中"两个子区域
2. "当前处理中"区域正确显示 daemon_state.json 中的当前 proposal 名称、项目、阶段、8 阶段进度条、开始时间；无任务时显示 Idle 提示
3. "排队中"区域正确列出 openspec/changes/ 下所有待处理 proposal，含序号、名称、项目、首行摘要；无排队时显示 Queue empty
4. 页面在 ≤768px 宽度下可用：卡片单列、hero 竖排、表格可读、进度条可横滚
5. 页面 HTML 中不存在对 `/api/status.json` 的 fetch 调用、`updateQueueSection` 函数、`<div id="queue-section">` 元素
6. 现有测试（`test_dashboard_api.py`, `test_dashboard_queue.py`）全部通过

### 验收方式
- `ruff check` 无 lint 错误
- `pytest tests/test_dashboard_api.py tests/test_dashboard_queue.py` 通过
- 手动在浏览器 ≤768px 视口下确认布局正确
- 确认页面源码中无 `/api/status.json` 相关代码

## 约束

### 不能修改的文件
- `daemon.py`（daemon 主循环）
- `daemon_state.json`（状态文件格式）
- `requirements.txt` / `pyproject.toml`（不引入新依赖）

### 项目部署分支
main

### 已知风险
- `daemon_state.json` 字段名可能随版本变化，需确认实际文件内容
- dashboard.html 可能由 Python 渲染生成而非静态文件，需确认修改位置（`zsiga/metrics/dashboard.py` vs `site/dashboard.html`）
- 阶段进度条的阶段顺序需与 daemon 实际阶段枚举严格对齐
- 清理 JS 逻辑时需避免误删其他有效的 `<script>` 代码

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考
