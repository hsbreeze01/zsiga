# Tasks: Dashboard 实时监控与异常诊断增强

## Group 1: Daemon State Persistence

- [x] 1.1 添加 `_write_daemon_state()` 辅助函数到 `zsiga/daemon.py`，在 daemon_loop 的每个阶段切换时写入 `data/daemon_state.json`（包含 pid、started_at、cycle、state、current_change、current_phase、current_project、last_heartbeat 字段），并在 loop 退出时将 state 置为 stopped

## Group 2: Dashboard 后端渲染逻辑

- [ ] 2.1 添加 `_render_daemon_card()` 函数到 `zsiga/dashboard.py`，读取 `data/daemon_state.json` 并生成 Daemon Status Card HTML（PID、Started At、Cycle、Processing、State badge、Dashboard URL；文件缺失时显示 Daemon Offline）
- [ ] 2.2 添加 `_render_failure_panel()` 函数到 `zsiga/dashboard.py`，从 `data/changes.json` 提取最近 10 个失败/回滚记录，从 `memory/learnings.jsonl` 匹配错误摘要，生成含 `<details>` 展开块的 HTML 面板
- [ ] 2.3 添加 `_render_trend_charts()` 函数到 `zsiga/dashboard.py`，调用 `metrics/collector.py` 的 `compute_rolling_rates` 获取最近 20 个 change 的成功率和耗时数据，生成纯 CSS sparkline 和柱状图 HTML
- [ ] 2.4 添加 `_inject_auto_refresh()` 函数到 `zsiga/dashboard.py`，在 HTML `<head>` 中插入 `<meta http-equiv="refresh" content="60">` 并在 header 区域添加 "Auto-refresh: 60s" 提示文字

## Group 3: Dashboard HTML 集成与样式

- [ ] 3.1 在 `zsiga/dashboard.py` 的主渲染流程中按正确顺序调用新增函数（auto-refresh → hero → daemon_card → metrics → phase_performance → failure_panel → trend_charts → milestones → journal），并在 `<style>` 中添加 daemon-card、failure-entry、sparkline、duration-chart 等新 CSS 类（scope: frontend+backend，含样式和模板拼接）

## Group 4: 测试

- [x] 4.1 添加 `tests/test_daemon_state.py`：测试 `_write_daemon_state` 正确写入所有字段、idle 状态置空、daemon 停止时 state=stopped、文件为空时的兜底处理
- [ ] 4.2 添加 `tests/test_dashboard_failure_panel.py` + `tests/test_dashboard_trends.py`：测试失败面板渲染（有失败/无失败/匹配 lesson/截断10条）和趋势图数据准备（成功率计算/耗时提取/缺失数据跳过）
