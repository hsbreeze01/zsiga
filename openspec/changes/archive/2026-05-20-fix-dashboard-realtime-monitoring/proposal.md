# Proposal: 修复 Dashboard 实时监控 — 落地未完成的 4 项缺失

## Summary
enhance-dashboard-realtime-monitoring 提案虽然标记为 DONE，但实际 dashboard 只生成了静态统计页面，以下 4 项核心功能未落地到 dashboard.html 中。本次修复需将它们全部实现。

## 问题清单

### P1. Daemon 实时状态卡片缺失
**现状**: data/daemon_state.json 已由 daemon.py 正确写入（pid, started_at, cycle, state, current_change, current_phase, last_heartbeat），但 dashboard.py 的 _render 函数完全没有读取和展示这个文件。dashboard 无法看到 daemon 当前在做什么。

**要求**: 在 hero 区域（mascot + level badge）下方、指标卡片网格之前，新增一个 Daemon 状态卡片行：
- PID | Started At | Current Cycle | State (running/resting) | Processing (显示 current_change 名称，空闲显示 "Idle")
- Next heartbeat / Last heartbeat 时间
- 从 data/daemon_state.json 读取，用 json.loads + Path.read_text

### P2. 失败诊断面板缺失
**现状**: learnings.jsonl 中有 pipeline.fail.* 和 code.* 类型的 lesson，changes 中有 outcome=reverted 的记录，但 dashboard 没有展示失败历史和根因。

**要求**: 在 Phase Performance 表格之后、Resource Usage 之前，新增一个 "🔍 Failure Diagnosis" 面板：
- 展示最近 10 个 outcome 为 reverted 或失败(verify/review fail)的 change
- 每个 failure 显示：change 名称、项目名、失败阶段、从 learnings.jsonl 匹配的最新 lesson takeaway、耗时、时间
- 用 HTML details/summary 可展开详情
- 如果该 change 有 openspec/changes/{name}/diagnosis.md 且非空，展示诊断内容

### P3. Sparkline 趋势未渲染
**现状**: metrics/collector.py 已有 compute_rolling_rates 函数，dashboard.py 已有 _sparkline_html 函数，但 _render 中从未调用。趋势图不存在。

**要求**: 在 Resource Usage 区域新增一个卡片：
- "📈 Success Trend" 卡片，调用 compute_rolling_rates + _sparkline_html 渲染最近 20 个 change 的成功率 sparkline
- "📈 Duration Trend" 卡片，用纯 CSS div（高度百分比）渲染最近 20 个 change 的耗时柱状图，颜色编码：成功绿、失败红

### P4. 页面自动刷新缺失
**现状**: dashboard 是纯静态 HTML，必须手动刷新浏览器才能看到更新。daemon 每分钟可能更新 daemon_state.json，但用户看不到变化。

**要求**: 在 _render 的 <head> 中加入 `<meta http-equiv="refresh" content="60">`，并在页面顶部加一行小字提示 "Auto-refresh: 60s"。

## Constraints
- 纯 HTML + CSS + 内联 JS（如果需要），不引入外部库
- 复用 dashboard.py 中已有的 helper 函数
- daemon_state.json 是只读消费，不要修改写入逻辑
- 所有修改在 zsiga/metrics/dashboard.py 中完成
- 实现后运行 pytest + ruff 确保通过
