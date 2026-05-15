# Proposal: L6 Autonomous Sense — 自主感知与提案

## Summary
在 zsiga 的 pipeline 前面增加自主感知层（Sense → Judge → Propose），使 zsiga 能自主巡检所有目标项目，发现异常、识别机会、生成 proposal 并执行，不再依赖人类创建 proposal。

## Motivation
当前 zsiga 是被动执行模式：人类创建 proposal.md → zsiga 扫描并执行 pipeline。L5 让 zsiga 能处理模糊人类指令，但仍然需要人类发起。

实际运维中存在大量可自动化的维护工作：服务健康检查、kline 采集缺失（如 5/13-5/14 的 misfire 事故）、lint 错误累积、重复失败模式。这些工作如果能被 zsiga 自主感知并修复，将大幅减少人工介入。

## Expected Behavior

### 感知信号源
- **健康检查**：定期 curl 各服务 health endpoint，检测 5xx/超时
- **Git 变更**：检测上次扫描后的新 commit、未合并分支、残留 .disabled 文件
- **日志异常**：journalctl 扫描 Traceback/Error 堆栈
- **质量度量**：ruff lint 新增错误、pytest 覆盖率变化
- **重复模式**：从 learnings.jsonl 提取出现 ≥3 次的 pattern_key

### 价值判断
- 信号按 CRITICAL/HIGH/MEDIUM/LOW/NOISE 五级评估
- 24h 去重窗口，避免重复 proposal 同一问题
- 每 cycle 最多 3 个 proposal，按优先级排序

### 自主提案
- 通过 Judge 的信号由 LLM 生成 proposal.md（符合 OpenSpec 格式）
- proposal 包含感知来源元数据（signal_source, detected_at, signal_priority）
- 生成的 proposal 进入现有 pipeline 正常执行

### Cycle 集成
- run_cycle() 开头增加 sense 阶段
- sense 生成的 proposal 与手动创建的 proposal 混合处理
- sense 配置通过 zsiga.yaml 新增的 sense 段控制
