# Proposal: Daemon 智能调度 — 有活就干、没活才睡

## Summary
将 daemon 的固定 8h cycle interval 改为智能调度：有 pending change 立即处理，处理完后短间隔轮询（5 分钟）等待新 proposal，新 proposal 出现后立即执行下一个 cycle。

## Motivation
当前 daemon.py 的 `daemon_loop()` 使用固定 8h 间隔休眠（第 217 行 `interval = config.pipeline.cycle_interval_hours * 3600`）。这导致：

1. **明明有活却干等** — 当前 2 个 pending change（evolve-learning + database-resource-management）需要等 8h 才被处理
2. **没活也在空转** — 即使没有任何新 proposal，每 8h 也会扫描一遍所有远端服务器
3. **响应性差** — 提交新 proposal 后最快也要等 8h 才有响应，实际体感是"扔进去没反应"

### 为何 zsiga 自己没有发现这个问题？

这是一个**自我感知盲区** — daemon 的 cycle interval 是启动时写死的配置参数，不是运行时错误。zsiga 没有"观察自身调度效率"的能力：
- 没有 metric 记录"cycle 开始时有几个 pending change"
- 没有 metric 记录"从 proposal 创建到开始处理的时间差"
- 没有 baseline 告诉它"8h 等待是否合理"

本质：**agent 缺乏对自身调度策略的元认知** — 它知道自己处理了什么 change，但不知道自己"浪费了多少等待时间"。

## Expected Behavior

### 调度逻辑改造

**当前逻辑（daemon.py 第 215-224 行）：**
```
while not shutdown:
    run_cycle()
    sleep(8h fixed)
```

**目标逻辑：**
```
while not shutdown:
    pending = run_cycle()  # 返回处理了多少 change
    if pending > 0:
        continue  # 有活就干，不睡，立即下一轮
    else:
        sleep(short_interval)  # 没活才睡，5 分钟轮询
```

### 具体改造点

1. **`orchestrator.run_cycle()` 返回值**：当前返回 None，改为返回 `processed_count`（本 cycle 处理了多少 change）
2. **`daemon_loop()` 调度逻辑**：
   - `processed_count > 0` → `continue`（立即下一轮，不睡）
   - `processed_count == 0` → sleep `idle_poll_minutes`（默认 5 分钟，从 config 读取）
   - 保留 `cycle_interval_hours` 作为 fallback，但只在 `idle_poll_minutes` 未配置时使用
3. **config 新增** `pipeline.idle_poll_minutes: 5`（默认值）
4. **安全阀**：连续运行超过 `max_continuous_cycles`（默认 20）强制休眠 `cooldown_minutes`（默认 30），防止无限循环消耗 API 额度

### daemon_state.json 增强

在 `_write_daemon_state()` 中新增：
- `total_cycles`: 累计 cycle 数
- `total_changes_processed`: 累计处理 change 数
- `idle_cycles`: 连续空转次数（用于安全阀）
- `last_change_at`: 上次处理 change 的时间

## Acceptance Criteria

1. 提交 proposal 后 daemon 在 `idle_poll_minutes` 内开始处理（而非 8h）
2. 多个 pending change 连续处理，不需要中间等待
3. 没有新 change 时，daemon 以 5 分钟间隔轮询
4. 安全阀生效：连续 20 个空 cycle 后强制冷却 30 分钟
5. 现有信号处理（SIGUSR1/2/TERM/INT）不受影响
6. `daemon_state.json` 包含新的统计字段
