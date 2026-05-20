# Proposal: Dashboard Auto-Refresh + Queue/Stage Real-Time Display

## Summary

当前 dashboard 是静态 HTML，60 秒整页刷新，且 pipeline 执行过程中（enrich→implement→review→verify→deliver）不更新 daemon_state.json 的 current_change/current_phase。用户在 pipeline 运行期间看不到任何进度。

需要两个改动：
1. **数据源**：orchestrator 每进入一个 phase 就主动写 daemon_state.json（推送）
2. **前端**：dashboard 通过 JS 定时 fetch API 拉取最新状态，局部刷新（拉取）

## Requirements

### 1. 数据源：orchestrator 每阶段推送状态（核心修复）
- 文件：`zsiga/pipeline/orchestrator.py`
- 在每个 phase 切换时（ENRICH/IMPLEMENT/REVIEW/VERIFY/REFLECT/DELIVER），调用 `_update_daemon_state(change_name, phase_name, project_name)`
- 具体位置：在每个 phase 的 print 语句后（如 `Phase 1 done`、`Phase 2 done` 等）之前，先写状态
- 实现：读取 `data/daemon_state.json`，更新 `current_change`/`current_phase`/`current_project`/`last_heartbeat`，写回文件
- 这是一个轻量写操作（读 JSON → 改 4 个字段 → 写回），不影响 pipeline 性能

### 2. API：daemon.py 提供 `/api/status.json`
- 文件：`zsiga/daemon.py`
- 在 HTTP handler 中新增 `/api/status.json` 端点
- 读取 `data/daemon_state.json` + 扫描 `openspec/changes/` 获取队列
- 返回 JSON：
  ```json
  {
    "daemon": { "pid", "state", "cycle", "current_change", "current_phase", "current_project", "heartbeat" },
    "queue": [
      { "name": "fix-xxx", "project": "zsiga", "summary": "Proposal: Fix ..." },
      ...
    ]
  }
  ```

### 3. 前端：JS fetch + 局部刷新，10 分钟间隔
- 文件：`zsiga/metrics/dashboard.py`（HTML 模板部分）
- 移除 `<meta http-equiv="refresh" content="60">`
- 页面加载后 JS `setInterval(fetchStatus, 600000)`，每 10 分钟 fetch `/api/status.json`
- 只更新动态区域（daemon status 卡片 + proposal queue 表格），不重载整页
- **Proposal Queue** 表格：每行显示 proposal 名称、所属项目、摘要
  - 正在处理的 proposal 高亮（黄色左边框）+ phase badge
  - 队列空时显示 "Queue empty — idle polling"
- **刷新指示器**：右上角 "Last refreshed: HH:MM:SS"

### 4. 静态 fallback
- `generate_dashboard()` 仍然生成完整静态 HTML（初次加载 + fallback）
- JS 加载后用 API 数据覆盖动态区域
- 如果 JS fetch 失败，静态内容仍然展示

## Architecture

```
orchestrator (pipeline)
    ↓ 每进入新 phase 时写 daemon_state.json（推送）
    
data/daemon_state.json  ←  实时状态文件
    
daemon.py (/api/status.json)
    ↓ 读取 daemon_state.json + 扫描 openspec/changes/
    
dashboard.html (JS fetch)
    ↓ 每 10 分钟拉取 /api/status.json（拉取）
    
浏览器展示
```

## Constraints
- Scope: project=zsiga
- 修改文件：`zsiga/pipeline/orchestrator.py`（phase 状态推送）、`zsiga/daemon.py`（API 端点）、`zsiga/metrics/dashboard.py`（JS + HTML）
- 不要引入前端框架，纯 vanilla JS
- 不要修改 git_ops
- 运行 pytest 确认不破坏现有测试
