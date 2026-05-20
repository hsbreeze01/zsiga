# Proposal: Dashboard Proposal Queue Panel

## Summary

在 dashboard 新增「📋 Proposal Queue」面板，实时展示：
1. 当前排队的 proposal 列表（名称、所属项目、proposal.md 首行摘要）
2. 正在处理的 proposal 及其所处阶段（当前 daemon section 已有 current_change，增强展示）

用户打开 `http://49.234.48.221:58175/dashboard.html` 即可看到 zsiga 的完整工作状态。

## Requirements

### 1. 新增 `_render_proposal_queue()` 函数
- 文件：`zsiga/metrics/dashboard.py`
- 扫描所有 target 项目的 `openspec/changes/` 目录（排除 `archive`）
- 对每个 proposal 目录，读取 `proposal.md` 首行（`# Title` 行）作为摘要
- 从 `proposal` 所在路径判断所属项目（本地路径 → target 项目名映射）

### 2. 队列面板 HTML 结构
在 daemon status section 下方，Phase Performance 上方插入：

```html
<div class="section">
  <h2>📋 Proposal Queue</h2>
  <table>
    <thead><tr><th>#</th><th>Proposal</th><th>Project</th><th>Summary</th></tr></thead>
    <tbody>
      <!-- 每行一个排队的 proposal -->
      <!-- 正在处理的 proposal 行高亮 + 显示当前 phase badge -->
    </tbody>
  </table>
  <!-- 无 proposal 时显示 "Queue empty — idle polling" -->
</div>
```

### 3. 当前处理 proposal 增强
- 已有的 daemon section 中 `Processing` 字段显示 `current_change (current_phase)`
- 在队列面板中，当前正在处理的 proposal 行加 `style="background:#1e293b;border-left:3px solid #f59e0b"` 高亮
- 旁边显示 phase badge（enrich/implement/review/verify/deliver）

### 4. 数据来源
- 队列数据：扫描 `zsiga.yaml` targets 中每个项目的 `openspec/changes/`（复用 `DirectoryScanner` 逻辑或直接读目录）
- 当前处理数据：已有 `data/daemon_state.json` 的 `current_change`/`current_phase`/`current_project`
- 注意：dashboard 是静态 HTML（60s 刷新），每次 `generate_dashboard()` 时重新扫描

### 5. 性能约束
- 扫描必须快速（`ls` + 读首行），不能拖慢 dashboard 生成
- 如果 target 是远程（SSH transport），使用已有的 transport 抽象

## Constraints
- Scope: project=zsiga
- 修改文件：`zsiga/metrics/dashboard.py`、`site/dashboard.html`（由 generate_dashboard 生成）
- 不要修改 daemon.py 或 scanner.py 的核心逻辑
- 不要引入新的依赖
- 保持现有 dashboard 的视觉风格（暗色主题、卡片布局）
- 运行 pytest 确认不破坏现有测试
