# Tasks: L6 Autonomous Sense

## Group 1: 感知引擎 (sensor.py)

- [ ] 1.1 创建 `zsiga/intake/sensor.py`：定义 Signal dataclass，实现 Sensor 类的 `scan()` 方法框架
- [ ] 1.2 实现 `_check_health()`：遍历配置的 endpoints，curl 检查 HTTP 状态码，返回 health_check Signal 列表
- [ ] 1.3 实现 `_check_git_changes()`：对比上次扫描的 HEAD SHA，检测新 commit，返回 git_changes Signal 列表
- [ ] 1.4 实现 `_check_logs()`：journalctl 扫描指定 service 的 Error/Traceback，返回 log_errors Signal 列表
- [ ] 1.5 实现 `_check_quality()`：运行 ruff check，对比上次结果，检测新增 lint 错误，返回 quality Signal 列表
- [ ] 1.6 实现 `_check_patterns()`：从 learnings.jsonl 统计 pattern_key 频次，超过阈值的返回 patterns Signal 列表

## Group 2: 价值判断 (judge.py)

- [ ] 2.1 创建 `zsiga/agent/judge.py`：定义 SignalPriority 枚举、JudgeResult dataclass
- [ ] 2.2 实现 `judge()` 主函数：接收 Signal 列表 + SenseHistory，执行去重 → 优先级评估 → 过滤 → 排序 → 截断
- [ ] 2.3 实现去重逻辑：基于 dedup_key (`{type}:{project}:{hash}`) 查询 SenseHistory，24h 内重复则跳过
- [ ] 2.4 实现优先级评估：health_check→HIGH, log_errors 含 OOM→CRITICAL, git_changes→LOW, quality→MEDIUM, patterns→MEDIUM

## Group 3: 自主提案 (proposer.py)

- [ ] 3.1 创建 `zsiga/intake/proposer.py`：实现 `propose()` 函数，遍历 JudgeResult 列表，对每个结果调用 LLM 生成 proposal.md
- [ ] 3.2 实现 proposal slug 生成和冲突检测：slugify(JudgeResult) → 检查 openspec/changes/{slug} 是否已存在 → 存在则追加数字后缀
- [ ] 3.3 实现 LLM prompt 构造：将 signal data + project_context 组装为 user_prompt，system_prompt 引导生成符合 OpenSpec 格式的 proposal（含 Meta 段）

## Group 4: 感知历史 (sense_history)

- [ ] 4.1 创建 `zsiga/memory/sense_history.py`：实现 SenseHistory 类，支持 `record(proposed/skipped)` 和 `is_recent(dedup_key, window_hours)` 查询
- [ ] 4.2 持久化到 `memory/sense_history.jsonl`：追加写入，加载时只读最近 7 天的记录

## Group 5: 配置体系

- [ ] 5.1 在 `zsiga/config.py` 新增 `SenseConfig`、`SignalConfig`、`HealthCheckConfig` 等配置类
- [ ] 5.2 修改 `load_config()` 解析 zsiga.yaml 中的 `sense:` 段，填充 SenseConfig
- [ ] 5.3 在 `zsiga.yaml` 添加完整的 sense 配置段（含注释）

## Group 6: Cycle 集成

- [ ] 6.1 修改 `zsiga/pipeline/orchestrator.py` 的 `run_cycle()`：在 scanner.scan() 前增加 sense 阶段调用
- [ ] 6.2 集成 sense_history 到 orchestrator：加载历史 → 传给 judge → 记录结果
- [ ] 6.3 增加 sense 阶段的日志输出：`[sense] found N signals, M judged, K proposed`

## Group 7: Milestone & 测试

- [ ] 7.1 在 `zsiga/metrics/types.py` 新增 MILESTONE_L6 定义（4 个信号源、10 个自主 proposal、60% 成功率、≤20% 误报率）
- [ ] 7.2 编写 `tests/test_sensor.py`：测试各信号检测器的 Signal 生成逻辑（mock transport）
- [ ] 7.3 编写 `tests/test_judge.py`：测试去重、优先级评估、速率限制
- [ ] 7.4 编写 `tests/test_proposer.py`：测试 slug 生成、冲突检测（mock LLM agent）
