# Clarify: dashboard-proposal-queue-mobile

## 需求拆解

### 原始需求
改造 dashboard 页面：合并两个 proposal queue 区块为统一的 Python 渲染面板（含当前处理进度条），添加手机端 `@media` 适配，删除失效的 JS fetch `/api/status.json` 逻辑及空占位 div。

### 拆解后的子任务
- [ ] 1. Proposal Queue 面板合并与渲染（预估复杂度：高, 预估 token：~6000 / 无历史参考）
  - 删除静态 `{proposal_queue_section}` 模板占位和空的 `<div id="queue-section">`
  - 在 `dashboard.py` 中新增渲染逻辑，读取 `daemon_state.json` 获取 `current_change` / `current_phase`，生成 Current 子区域 HTML（含 8 阶段进度条：CLARIFY→ENRICH→IMPLEMENT→REVIEW→VERIFY→OPTIMIZE→REFLECT→DELIVER，当前高亮、已完成标绿、未到灰色）
  - 在 `dashboard.py` 中扫描 `openspec/changes/` 目录获取排队 proposals，生成 Queued 子区域 HTML（序号、名称、项目、摘要）
  - 无数据时分别显示 Idle / Queue empty 占位文案

- [ ] 2. 手机端 @media 响应式适配（预估复杂度：中, 预估 token：~2500 / 无历史参考）
  - 在 `<style>` 块中添加 `@media (max-width: 768px)` 规则：body padding、.grid 单列、h1 字号、hero 竖排、table 字号与 padding、.card .value 字号、.phase-progress 横滚

- [ ] 3. 清理失效 JS 逻辑（预估复杂度：低, 预估 token：~800 / 无历史参考）
  - 删除 `<script>` 中 `fetch('/api/status.json')` 调用及 `updateQueueSection` 函数
  - 删除 `<div id="queue-section">` 空 div

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中的模板渲染逻辑
- 修改 `site/dashboard.html` 的 CSS（@media）和 JS（删除死代码）
- 8 阶段进度条 UI 组件
- 从 `daemon_state.json` 和 `openspec/changes/` 目录读取数据

### OUT of scope
- 新增 API 端点（如 `/api/status.json`）
- 修改 `daemon.py` 或其他 daemon 文件
- 后端 Python 端点或路由变更
- 修改 dashboard 之外的其他页面

### 依赖的外部条件
- `daemon_state.json` 文件格式包含 `current_change`、`current_phase`、`heartbeat` 字段
- `openspec/changes/` 目录下每个子目录包含 `proposal.md` 文件，首行为 `# Title` 格式
- 现有 `dashboard.py` 的渲染函数结构（`{proposal_queue_section}` 占位符位置）

## 目标

### 成功标准
1. 页面仅有一个 proposal queue 面板，由 Python 完整渲染，无重复区块
2. Current 子区域正确显示当前处理中的 proposal 名称、项目、阶段，以及 8 阶段进度条（当前高亮、已完成标绿）
3. Queued 子区域列出所有待处理 proposal 的序号、名称、项目、摘要
4. 手机端（≤768px）卡片单列、hero 竖排、阶段进度条可横滚，页面可读可用
5. 不存在对 `/api/status.json` 的 fetch 调用和 `updateQueueSection` 函数
6. 不存在空的 `<div id="queue-section">`

### 验收方式
- 用浏览器 DevTools 移动模拟器（375px 宽度）检查布局，确认单列且无溢出
- 检查页面源码，确认无 `/api/status.json` 引用
- 在有/无 `daemon_state.json` 数据两种情况下分别验证面板显示
- ruff check 通过，无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py`
- `zsiga/daemon/` 目录下所有文件
- 任何新增 API 路由文件

### 项目部署分支
main

### 已知风险
- `daemon_state.json` 字段名可能变化，需在代码中做 key 缺失防护（`.get()` 带默认值）
- `proposal.md` 首行格式可能不统一（无 `#` 或为空），摘要提取需做 fallback
- 阶段进度条的 stage 列表需与 daemon 实际使用的阶段名严格对应

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考
