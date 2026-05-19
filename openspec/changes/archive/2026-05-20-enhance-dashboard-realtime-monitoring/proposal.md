# Proposal: Dashboard 实时监控与异常诊断增强

## Summary
为 zsiga dashboard 新增三个核心模块：Daemon 运行状态卡片、异常诊断面板、Rolling 趋势图。当前 dashboard 只有历史统计，缺少实时运行监控和异常问题排查能力。

## Motivation
zsiga 已部署为 daemon 运行在 49 上，Sisyphus（编排者）需要通过 dashboard 实时了解：
1. daemon 当前是否在运行、在处理什么、下次 cycle 何时开始
2. 任务失败时能快速定位根因和修复历史
3. 质量趋势是否在恶化（连续失败、耗时飙升）

当前 dashboard 缺少这三个能力，导致监控盲区。

## Expected Behavior

### 1. Daemon 状态卡片（顶部 hero 区域下方，指标卡片之前）
- PID：当前 daemon 进程 ID
- Started At：daemon 启动时间
- Current Cycle：当前第几个 cycle
- Processing：正在处理的 change 名称（如空闲则显示 Idle / Next cycle in Xh）
- State：running / paused / stopped
- Dashboard URL：当前 dashboard 访问地址

实现方式：daemon 每次进入新阶段时写 data/daemon_state.json：
  - pid, started_at, cycle, state
  - current_change, current_phase, current_project
  - last_heartbeat（每次循环迭代更新）

### 2. 异常诊断面板（Phase Performance 之后，Evolution Roadmap 之前）
- 展示最近 10 个失败或回滚的 change
- 每个 failure 显示：
  - change 名称 + 项目
  - 失败阶段（enrich/implement/verify/deliver）
  - 错误摘要（从 learnings.jsonl 提取，取最新一条匹配的 lesson）
  - 修复尝试次数
  - 耗时
  - 时间
- 可点击展开查看完整错误上下文（用 HTML details/summary 标签）

实现方式：从 memory/learnings.jsonl 提取 failure 相关的 lesson，与 data/changes.json 中 outcome=reverted 或 outcome=fail 的记录关联。

### 3. Rolling 趋势图（异常诊断面板之后）
- 成功率趋势：最近 20 个 change 的 rolling success rate sparkline
- 耗时趋势：最近 20 个 change 的耗时柱状图（用纯 CSS div 实现，不用外部库）
- 颜色编码：成功绿色、失败红色、超时黄色

实现方式：metrics/collector.py 已有 compute_rolling_rates 函数，直接复用。耗时数据在 data/changes.json 的 started_at/finished_at 字段中。

### 4. 页面自动刷新
- HTML meta http-equiv=refresh content=60 实现每 60 秒自动刷新
- 页面顶部显示 Auto-refresh: 60s 提示

## Constraints
- 不引入任何前端框架或外部 JS 库，纯 HTML 加 CSS
- dashboard.py 中已有的 helper 函数（_rate_class, _fmt_tokens, _fmt_seconds 等）必须复用
- daemon_state.json 写入要在 daemon.py 的 daemon_loop 中完成，每个阶段切换时更新
- 所有改动完成后必须 git commit 并 git push 到远端
