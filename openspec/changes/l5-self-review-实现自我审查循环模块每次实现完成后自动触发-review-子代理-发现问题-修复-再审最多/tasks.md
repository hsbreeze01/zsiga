# tasks.md — l5-self-review: 自我审查循环模块

## 1. 审查循环核心逻辑

- [x] 1.1 在 `zsiga/agent/reviewer.py` 中新增 `ReviewLoopResult` dataclass 和 `run_review_loop()` 函数
  - `ReviewLoopResult` 包含：final_verdict, rounds_executed, fix_attempts, elapsed_seconds, last_issues, had_critical
  - `run_review_loop()` 封装循环：调用 `run_review()` → `parse_review_verdict()` → 判断是否需要修复 → 修复 → 重新审查
  - SUGGESTION-only 视为通过，只有 CRITICAL 触发修复
  - 修复使用 `agent.run()` 执行，受限 changed_files 约束
  - 预估 3 轮（读现有 reviewer.py + 写新函数 + 验证 ruff）

## 2. Orchestrator 集成

- [x] 2.1 修改 `zsiga/pipeline/orchestrator.py` 的 `_run_phases()` 方法，在 IMPLEMENT 成功后、VERIFY 之前插入 REVIEW 阶段
  - 导入 `run_review_loop` 和 `ReviewLoopResult`
  - 在 mechanical verification 通过后、VERIFY 阶段前调用 `run_review_loop()`
  - 将审查结果记录为 `PhaseRecord(phase=Phase.REVIEW, ...)`
  - 添加 `_summarize_issues()` 辅助函数，提取 issues 摘要（≤200 字符）
  - 打印审查进度和结果日志
  - 预估 3 轮（读 orchestrator + 编辑 _run_phases + 验证 ruff）

## 3. 配置校验增强

- [ ] 3.1 在 `zsiga/config.py` 的 `validate_config()` 中添加 `review_max_rounds` 范围校验
  - 当 `review_max_rounds` 不在 [1, 5] 范围时添加 warning
  - 预估 2 轮（读 config.py + 编辑 validate_config + 验证）

## 4. 测试

- [ ] 4.1 新增 `tests/test_reviewer.py`，测试审查循环的纯逻辑
  - 测试 `parse_review_verdict()` 对 CLEAN / ISSUES_FOUND / UNKNOWN 三种 verdict 的解析
  - 测试 `parse_review_verdict()` 对 CRITICAL 和 SUGGESTION issues 的解析
  - 测试 `ReviewLoopResult` dataclass 字段
  - 测试 `run_review_loop()` 的 round counting 逻辑（mock run_review 和 parse_review_verdict）
  - 测试 SUGGESTION-only 场景不触发修复
  - 测试 max_rounds 耗尽后正常返回
  - 预估 3 轮（写测试文件 + 验证 pytest）
