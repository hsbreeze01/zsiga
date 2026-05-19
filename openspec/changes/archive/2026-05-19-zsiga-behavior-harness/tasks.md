## 1. Harness 基础设施

- [ ] 1.1 创建 `zsiga/harness/__init__.py` 包结构，导出 `run_capability_tests`、`run_behavioral_tests`、`run_regression`、`run_qualification`
- [ ] 1.2 创建 `zsiga/harness/conftest.py`，提供公共 fixtures（mock LLM client、mock transport、临时 git repo）
- [ ] 1.3 创建 `zsiga/harness/runner.py`，实现 `HarnessRunner` 类：发现并执行测试、收集结果、emit event、写入 JSONL
- [ ] 1.4 在 `zsiga/metrics/db.py` 中新增 `harness_results` 表（id, ts, change_name, suite, pass_count, fail_count, failed_tests_json, duration_seconds）

## 2. Capability Tests（能力单元测试）

- [ ] 2.1 创建 `zsiga/harness/capability/test_intent_router.py`：>= 20 测试用例，覆盖六大意图 + 消歧 + 中英混合 + 边界（空输入、ambiguous）
- [ ] 2.2 创建 `zsiga/harness/capability/test_dispatch.py`：验证 6 种 IntentType 路由到正确执行路径（mock orchestrator 方法调用）
- [ ] 2.3 创建 `zsiga/harness/capability/test_recovery.py`：验证 RecoveryManager rollback、fix loop 次数限制、EscalationManager abort 触发
- [ ] 2.4 创建 `zsiga/harness/capability/test_parallel_pool.py`：验证 dispatch_many/collect_all 并发执行、单个任务失败不影响其他、timeout 隔离
- [ ] 2.5 创建 `zsiga/harness/capability/test_reviewer.py`：验证 run_review 调用流程、parse_review_verdict 对 CLEAN/ISSUES/UNKNOWN 的解析
- [ ] 2.6 创建 `zsiga/harness/capability/test_skill_evolution.py`：验证 pattern 提取、rule 生成、learnings 输入输出

## 3. Behavioral Tests（边界 & 对抗）

- [ ] 3.1 创建 `zsiga/harness/behavioral/test_budget_resilience.py`：phase isolation、zero budget、per-turn overflow、compaction trigger
- [ ] 3.2 创建 `zsiga/harness/behavioral/test_intent_adversarial.py`：>= 10 对抗用例（triple collision、keyword stuffing、nested clause、中英混合、矛盾意图）
- [ ] 3.3 创建 `zsiga/harness/behavioral/test_tool_errors.py`：read_file 不存在路径、git_ops 无 commit repo、transport 连接失败

## 4. Regression Runner（回归执行器）

- [ ] 4.1 实现 `zsiga/harness/runner.py` 的 `run_regression()` 函数：收集 capability + behavioral 测试结果、写入 JSONL event、持久化到 DB
- [ ] 4.2 修改 `zsiga/pipeline/orchestrator.py`：在 `_run_phases` 的 finally 块中调用 `run_regression(change_name)`
- [ ] 4.3 新增 CLI 命令 `zsiga harness run`（跑全量测试）和 `zsiga harness regression`（跑回归 + 输出报告）

## 5. Level Qualification（级别认证）

- [ ] 5.1 创建 `zsiga/harness/level/test_l5_qualification.py`：端到端 pipeline、intent accuracy >= 90%、6 路由正确、recovery、budget isolation
- [ ] 5.2 实现 `run_qualification(level)` 函数：运行对应级别测试、返回 pass/fail 结果
- [ ] 5.3 修改 `zsiga/metrics/collector.py` 的 `check_milestone`：量化达标后调用 qualification，两者都通过才标记 achieved
- [ ] 5.4 修改 `zsiga/metrics/db.py` 的 `save_level_snapshot`：新增 `qualification_results` 字段
- [ ] 5.5 新增 CLI 命令 `zsiga harness qualify --level L5`

## 6. 集成 & 验证

- [ ] 6.1 运行全量 harness（`zsiga harness run`），确认所有测试通过
- [ ] 6.2 用 zsiga propose 跑一个真实 change，验证 post-change regression 自动触发
- [ ] 6.3 运行 `zsiga harness qualify --level L5`，验证 L5 认证通过
- [ ] 6.4 更新 dashboard 展示 harness 通过率
