# Clarify: dashboard-proposal-queue-mobile

## 需求拆解

### 原始需求
改造 dashboard 的 Proposal Queue 区域：合并静态渲染与失效 JS 动态渲染为统一的 Python 渲染面板（含当前处理进度条 + 排队列表）；删除不存在的 `/api/status.json` fetch 逻辑及空占位 div；添加移动端 `@media` 适配使页面在手机上可用。

### 拆解后的子任务

- [ ] 1. **合并 Proposal Queue 面板为 Python 渲染** (预估复杂度：高, 预估 token：~6000 / 无历史参考)
  - 删除模板中 `{proposal_queue_section}` 静态区块和 `<div id="queue-section">` 空占位
  - 新增 Python 函数读取 `data/daemon_state.json` 提取 `current_change` / `current_phase` / `heartbeat`
  - 扫描 `openspec/changes/` 目录获取排队中的 proposal（解析 proposal.md 首行标题）
  - 渲染 Current 子区域：proposal 名称、项目、当前阶段、开始时间；无任务时显示 Idle
  - 渲染 Queued 子区域：序号、名称、项目、摘要；无队列时显示 Queue empty
  - 文件范围：`zsiga/metrics/dashboard.py`

- [ ] 2. **阶段进度条组件** (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 在 CSS 中添加 `.phase-progress` / `.phase-step` 样式
  - 渲染 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER` 水平进度条
  - 已完成阶段标绿、当前阶段高亮、未来阶段灰色
  - 手机端通过 `overflow-x: auto` 横滚
  - 文件范围：`zsiga/metrics/dashboard.py`（内联 CSS + HTML 生成）

- [ ] 3. **移动端 @media 适配** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 在 `<style>` 中添加 `@media (max-width: 768px)` 块
  - 覆盖：body padding、grid 单列、h1 字号、hero 竖排、table 字号与 padding、card value 字号
  - 文件范围：`zsiga/metrics/dashboard.py`（内联 style 部分）

- [ ] 4. **删除失效 JS fetch 逻辑** (预估复杂度：低, 预估 token：~1000 / 无历史参考)
  - 删除 `<script>` 中 `fetch('/api/status.json', ...)` 调用和 `updateQueueSection` 函数
  - 删除 `<div id="queue-section">` 空 div
  - 文件范围：`zsiga/metrics/dashboard.py`（内联 script + HTML 部分）

## 边界

### IN scope
- 合并 Proposal Queue 为 Python 端统一渲染（Current + Queued 两个子区域）
- 阶段进度条可视化（8 阶段：CLARIFY → DELIVER）
- 移动端 `@media (max-width: 768px)` 响应式适配
- 删除失效的 `/api/status.json` fetch 及空占位 div
- 读取 `data/daemon_state.json` 和扫描 `openspec/changes/` 获取数据

### OUT of scope
- 新增 API 端点（如 `/api/status.json`）
- 修改 `daemon.py` 或 daemon 主循环逻辑
- 修改 `site/dashboard.html`（该文件由 Python 脚本生成）
- 后端 WebSocket 实时推送
- 修改非 dashboard 相关的页面或功能

### 依赖的外部条件
- `data/daemon_state.json` 文件存在且包含 `current_change` / `current_phase` / `heartbeat` 字段
- `openspec/changes/` 目录结构中每个子目录包含 `proposal.md`
- `zsiga/metrics/dashboard.py` 是 `site/dashboard.html` 的唯一生成源

## 目标

### 成功标准
1. dashboard 页面只有一个 Proposal Queue 面板，包含 Current 和 Queued 两个子区域
2. Current 区域正确显示 daemon 当前处理的 proposal 及 8 阶段进度条（高亮当前、绿色已完成、灰色未到）
3. Queued 区域列出所有待处理 proposal 的序号、名称、项目、摘要
4. 无任务时 Current 显示 "💤 Idle"、无队列时 Queued 显示 "Queue empty"
5. 页面在 ≤768px 宽度下可用（单列布局、表格可读、进度条可横滚）
6. 页面 `<script>` 中无对 `/api/status.json` 的 fetch 调用
7. HTML 中无 `<div id="queue-section">` 空 div

### 验收方式
- 检查生成的 `site/dashboard.html` 包含统一的 queue 面板 HTML 结构
- 确认无 `fetch('/api/status.json'` 字符串
- 确认无 `id="queue-section"` div
- 确认 `@media (max-width: 768px)` 存在于 `<style>` 中
- 确认 8 个阶段名称均出现在进度条 HTML 中
- 运行 `pytest tests/test_dashboard_api.py tests/test_dashboard_queue.py` 通过
- `ruff check zsiga/metrics/dashboard.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py`
- `site/dashboard.html`（由 Python 脚本生成，不应手动编辑）
- `zsiga/metrics/` 目录下除 `dashboard.py` 外的文件
- `data/daemon_state.json`（只读）

### 项目部署分支
main

### 已知风险
- `daemon_state.json` 可能不存在（首次运行前）——需要优雅降级显示 Idle
- `openspec/changes/` 中某些子目录可能没有 `proposal.md`——需要跳过或容错
- 内联 CSS/HTML 模板维护性较差——后续可考虑模板引擎，但本次 scope 内不涉及
- 阶段名称硬编码 8 个，如 daemon 增减阶段需同步更新

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考
