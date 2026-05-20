# Clarify: dashboard-proposal-queue-mobile

## 需求拆解

### 原始需求
改造 dashboard 的 Proposal Queue 区域，将静态渲染和失效的 JS 动态渲染合并为一个统一的 Python 渲染面板（含当前处理状态+排队列表），删除失效的 JS fetch 逻辑，并对整个页面做手机端响应式适配。

### 拆解后的子任务

- [ ] 1. **统一 Proposal Queue 面板（Python 渲染）** (预估复杂度：高, 预估 token：~6000 / 无历史参考)
  - 删除模板中 `{proposal_queue_section}` 占位符和 `<div id="queue-section">` 空 div
  - 新增 Current 子区域：读取 `daemon_state.json` 的 `current_change` / `current_phase` / heartbeat 时间，渲染正在处理的 proposal 信息
  - 新增 Queued 子区域：扫描 `openspec/changes/` 目录，列出所有待处理 proposal（名称、项目、proposal.md 首行标题）
  - 空状态处理：无 current 时显示 idle 提示，无 queued 时显示 empty 提示
  - 涉及文件：`zsiga/metrics/dashboard.py`（Python 端渲染逻辑 + HTML 模板片段）

- [ ] 2. **阶段进度条组件** (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 实现 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER` 阶段条
  - 当前阶段高亮，已完成阶段标绿（#22c55e），未到阶段灰色（#475569）
  - 添加 `.phase-progress` 容器样式
  - 涉及文件：`zsiga/metrics/dashboard.py`（模板中内联 CSS + HTML）

- [ ] 3. **删除失效 JS fetch 逻辑** (预估复杂度：低, 预估 token：~1000 / 无历史参考)
  - 删除 `<script>` 中对 `/api/status.json` 的 fetch 调用
  - 删除 `updateQueueSection` 函数
  - 删除 `<div id="queue-section">` 占位元素
  - 涉及文件：`zsiga/metrics/dashboard.py`（模板字符串）

- [ ] 4. **手机端响应式适配** (预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 在 `<style>` 中添加 `@media (max-width: 768px)` 查询
  - 卡片网格单列、hero 竖排、表格字号缩小、阶段进度条横滚
  - 涉及文件：`zsiga/metrics/dashboard.py`（模板 `<style>` 区块）

## 边界

### IN scope
- 统一 Proposal Queue 为单一 Python 渲染面板
- 显示当前处理中的 proposal（从 daemon_state.json 读取）
- 显示排队中的 proposal（从 openspec/changes/ 扫描）
- 阶段进度条可视化
- 删除失效的 JS fetch 和空 div
- 全页面移动端响应式 @media 适配

### OUT of scope
- 新增 /api/status.json 端点或任何后端 API
- 修改 daemon.py 或 daemon 主循环逻辑
- 修改 dashboard 以外的任何 Python 模块
- 实时 WebSocket 推送（仅页面刷新时更新）
- 新增 Python 依赖

### 依赖的外部条件
- `daemon_state.json` 文件格式稳定，包含 `current_change` / `current_phase` 字段
- `openspec/changes/` 目录结构稳定（每个子目录含 `proposal.md`）
- `site/dashboard.html` 可继续由 `zsiga/metrics/dashboard.py` 生成输出

## 目标

### 成功标准
1. dashboard 页面只有一个 Proposal Queue 区块，由 Python 渲染，无重复区块
2. 当前处理中的 proposal 正确显示名称、项目、阶段、进度条、开始时间
3. 排队中的 proposal 列表正确展示序号、名称、项目、摘要
4. 页面源码中无 `/api/status.json` 的 fetch 调用，无 `updateQueueSection` 函数，无 `<div id="queue-section">`
5. 在 768px 以下视口，卡片单列、hero 竖排、表格缩小、进度条可横滚
6. 阶段进度条正确高亮当前阶段，已完成阶段标绿

### 验收方式
- 浏览器打开 `site/dashboard.html`，检查 queue 面板渲染正确
- 浏览器 DevTools 切换移动端视口，确认响应式布局生效
- `grep -r "status.json" site/dashboard.html` 返回空
- `grep -r "queue-section" site/dashboard.html` 返回空
- `grep -r "updateQueueSection" site/dashboard.html` 返回空

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（daemon 主循环不改动）
- 任何非 dashboard 相关的 Python 模块
- `requirements.txt` / `pyproject.toml`（不新增依赖）

### 项目部署分支
- main

### 已知风险
- `daemon_state.json` 字段名可能变更或缺失，渲染时需做防御性读取（get 默认值）
- `openspec/changes/` 下某些目录可能无 `proposal.md`，需 try-except 跳过
- dashboard.py 中的 HTML 模板为 Python 字符串拼接，改动需注意转义和缩进一致性

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考
