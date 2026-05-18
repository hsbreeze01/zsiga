# Proposal: l4-diagnoser

## Problem

verify 阶段失败后，zsiga 当前的行为是盲目 retry（用相同策略重试），缺乏结构化的诊断循环。这导致：
- 多次重复相同修复尝试，浪费 turns
- 没有假设驱动的定向探测
- 失败原因不明，难以改进

## Scope

- **zsiga 自身项目**（self-modify）
- 新建 `zsiga/pipeline/diagnoser.py`
- 可能修改 `zsiga/pipeline/orchestrator.py`（集成调用点）

## Approach

实现结构化诊断循环 `Diagnoser`：

1. verify 失败 → 触发 diagnose 阶段
2. `hypothesize()` — 基于失败信息生成 3-5 个排序假设（根因候选）
3. `instrument()` — 对每个假设做最小化探测（如 read 文件、run diagnostic 命令）
4. `targeted_fix()` — 基于探测结果选择最可能的根因，生成定向修复方案
5. 返回修复方案给 IMPLEMENT 阶段使用

关键设计：
- 假设按可能性排序（从错误信息中提取线索）
- 探测是只读的（不修改任何文件）
- 每次最多探测 3 个假设，避免浪费 turns
- 生成 DiagnosisReport 记录到 metrics

## Success Criteria

1. `zsiga/pipeline/diagnoser.py` 文件存在且可 import
2. `Diagnoser` 类有 `hypothesize()`, `instrument()`, `targeted_fix()` 方法
3. L4 capability task `diagnose_mode` 的 deliverable `pipeline/diagnoser.py` 被验证器识别为已完成
