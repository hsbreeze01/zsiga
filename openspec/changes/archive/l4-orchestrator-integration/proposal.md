# Proposal: l4-orchestrator-integration

## Problem

zsiga 已实现 intent_router、task_decomposer、escalation 三个模块，但它们尚未集成到 orchestrator pipeline 中。三个模块独立存在但从未被 orchestrator 调用。

L4 capability tasks 的 deliverable 要求这些集成存在于 orchestrator 中：
- `intent_router.py` + `router: classify() → route()` → 需要 orchestrator 在处理 change 前调用 intent classification
- `task_decomposer.py` + `orchestrator: decompose() → dispatch_parallel() → aggregate()` → 需要 orchestrator 支持跨项目任务分解
- `escalation.py` + `orchestrator: escalate() with strategy rotation` → 需要 orchestrator 在修复失败时调用 escalation protocol

## Scope

- **zsiga 自身项目**（self-modify）
- 修改 `zsiga/pipeline/orchestrator.py`（主要集成点）
- 可能需要修改 `zsiga/__main__.py`（新命令入口）

## Approach

### 1. Intent Router 集成

在 `run_cycle()` 或 `_process_change()` 开头加入意图分类：
- 读取 proposal.md 内容
- 调用 `intent_router.classify(proposal_content)` 获取 Intent
- 根据 route 结果选择执行路径（pipeline / explore / ask_user）
- 记录意图分类到 PhaseRecord.detail

### 2. Task Decomposer 集成

在 `run_cycle()` 中加入跨项目任务分解支持：
- 当 proposal 涉及多个 project 时，调用 `task_decomposer.decompose()`
- 返回 Decomposition 后，按 parallel_groups 并行派发子任务
- 汇总各子任务结果到统一报告

### 3. Escalation Protocol 集成

在 `_run_phases()` 的修复循环中集成 escalation：
- 修复失败时记录 FailureRecord
- 调用 `escalation.next_strategy()` 获取下次修复策略
- 超过 MAX_ATTEMPTS 后生成 DiagnosisReport 并暂停

## Success Criteria

1. orchestrator.py 中有对 intent_router.classify() 的调用
2. orchestrator.py 中有对 task_decomposer.decompose() 的调用（或 _process_change 支持跨项目）
3. orchestrator.py 中有对 escalation protocol 的集成（strategy rotation + diagnosis report）
4. 所有修改后 tests 通过 + lint clean
