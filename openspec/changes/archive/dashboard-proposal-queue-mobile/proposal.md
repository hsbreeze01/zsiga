# Proposal: dashboard-proposal-queue-mobile

## Summary
改造 dashboard 的 Proposal Queue 区域和当前处理状态展示，并做手机端兼容性改造。

## Motivation
当前 dashboard 有两个问题：
1. 页面上有两个 proposal queue 区块——一个是 Python 静态渲染的（有数据），一个是 JS 动态渲染的（永远空，因为 /api/status.json 不存在）。需要合并为一个，且实时展示当前处理进度。
2. 页面没有手机端适配，在移动设备上不可用。

## Expected Behavior

### 1. Proposal Queue 面板（合并为一个）

删除静态渲染的 `{proposal_queue_section}` 和空的 `<div id="queue-section">`，改为统一由 Python 渲染一个完整的 queue 面板，包含两个子区域：

#### 1a. 当前处理中（Current）
显示 daemon 正在处理的 proposal（从 daemon_state.json 的 `current_change` 字段读取）：
- Proposal 名称
- 所属项目
- 当前所处阶段（从 daemon_state.json 的 `current_phase` 读取）
- 阶段进度条：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，当前阶段高亮，已完成的阶段标绿，未到的灰色
- 开始时间（heartbeat 时间）
- 如果没有正在处理的 proposal，显示 "💤 Idle — 等待下一个 proposal"

#### 1b. 排队中（Queued）
显示所有待处理的 proposal（从 scanner 扫描 openspec/changes/ 目录获得）：
- 序号
- Proposal 名称
- 所属项目
- 一行摘要（从 proposal.md 的第一行 # 标题提取）

如果没有排队的 proposal，显示 "Queue empty"。

### 2. 手机端兼容性改造

在 `<style>` 中添加 `@media` 查询：

```css
@media (max-width: 768px) {
  body { padding: 1rem; }
  .grid { grid-template-columns: 1fr; }
  h1 { font-size: 1.2rem; }
  .hero { flex-direction: column; gap: 1rem; }
  table { font-size: 0.75rem; }
  th, td { padding: 0.4rem 0.6rem; }
  .card .value { font-size: 1.4rem; }
  /* 阶段进度条在手机上横滚 */
  .phase-progress { overflow-x: auto; }
}
```

关键改动点：
- 卡片网格从 auto-fit 变为单列
- 表格字号缩小
- hero 区域竖排
- 阶段进度条可横滚

### 3. 删除失效的 JS fetch 逻辑

删除 `<script>` 中对 `/api/status.json` 的 fetch 调用和 `updateQueueSection` 函数（该 API 端点不存在，fetch 永远 404）。删除 `<div id="queue-section">` 这个空的占位 div。

## Constraints
- Scope: project=zsiga
- 只修改 `zsiga/metrics/dashboard.py`
- 不需要修改 daemon.py 或新增 API 端点
- Python 渲染时直接读取 daemon_state.json 获取当前状态
- 保持页面深色主题风格
