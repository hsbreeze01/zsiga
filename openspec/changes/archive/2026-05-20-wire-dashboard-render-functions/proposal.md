# Proposal: Dashboard 渲染接入 — 将已实现但未调用的函数接入 _render

## Summary
上一个 fix-dashboard-realtime-monitoring 提案中，4 个功能的函数逻辑已在 dashboard.py 中实现，但 _render() 主函数没有调用它们。dashboard.html 没有任何变化。本次只需做接入工作。

## 已实现但未接入的函数

用 `grep -n` 确认以下函数存在：

1. **`_daemon_status_section()`** — 约第 25 行，读取 data/daemon_state.json，返回 daemon 状态卡片 HTML
2. **`_failure_diagnosis_section()`** — 约第 88 行，读取失败 change + learnings，返回诊断面板 HTML  
3. **`_sparkline_html()`** — 约第 753 行，已有 rolling rate sparkline 渲染

## 具体要求

在 `dashboard.py` 的 `_render()` 函数中做以下 4 处修改：

### 1. 接入 Daemon 状态卡片
在 `_render` 函数体中，找到 hero div 结束后的位置，在 `<div class="grid">` 指标卡片之前，插入：
```python
daemon_section = _daemon_status_section()
```
并在 return 的 f-string 中，在 hero div 和 grid div 之间插入 `{daemon_section}`

### 2. 接入失败诊断面板
在 Phase Performance section 和 Resource Usage section 之间，插入：
```python
failure_section = _failure_diagnosis_section()
```
并在 return 的 f-string 中对应位置插入 `{failure_section}`

### 3. 接入 Sparkline 趋势
在 Resource Usage 的 grid 中（或之后新增一个 section），调用：
```python
from .collector import compute_rolling_rates
rates = compute_rolling_rates()
sparkline = _sparkline_html(rates)
```
渲染为卡片加入页面

### 4. 添加 auto-refresh meta
在 _render 的 `<head>` 中 `<meta charset="utf-8">` 之后加入：
```html
<meta http-equiv="refresh" content="60">
```
在 `<body>` 开头加入一行提示：
```html
<div style="text-align:right;font-size:0.7rem;color:#475569;margin-bottom:0.5rem">Auto-refresh: 60s</div>
```

## Constraints
- 只修改 _render() 函数体和 return 的 f-string，不新增函数
- 如果 _daemon_status_section 或 _failure_diagnosis_section 不存在或签名不对，先读取确认再调用
- 不要修改 daemon_state.json 的写入逻辑
- 不要修改 collector.py
- 修改后运行 pytest + ruff
- 确认 site/dashboard.html 被重新生成（daemon 会在 cycle 结束时调用 generate_dashboard，也可手动运行 python -c "from zsiga.metrics.dashboard import generate_dashboard; generate_dashboard()" 验证）
PROPOSAL_EOF