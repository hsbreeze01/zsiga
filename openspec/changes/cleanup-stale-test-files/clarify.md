# cleanup-stale-test-files — 需求契约

## 需求拆解

### 原始需求
删除 `tests/` 目录下所有 `test_spec_*` 文件（共 26 个），这些文件由已归档或已删除 proposal 的 VERIFY 阶段生成，污染每次新 proposal 的全量测试运行。

### 拆解后的子任务
- [ ] 1. 删除已归档 proposal 的 test_spec_* 文件（预估复杂度：低, 预估 token：~1200 / 无历史参考）
  - `test_spec_add_health_check_endpoint__health_check_endpoint.py`
  - `test_spec_add_health_check_endpoint__health_check.py`
  - `test_spec_add_proposal_stats_to_dashboard__proposal_stats_endpoint.py`
  - `test_spec_add_uptime_to_status_api__uptime_seconds_field.py`
  - `test_spec_dashboard_add_feedback_loop_metrics__dashboard_feedback_loop_section.py`
  - `test_spec_dashboard_add_feedback_loop_metrics__feedback_loop_metrics.py`
  - `test_spec_dashboard_add_feedback_loop_metrics__learning_injection_tracking.py`
- [ ] 2. 删除已删除 proposal 的 test_spec_* 文件（预估复杂度：低, 预估 token：~1200 / 无历史参考）
  - `test_spec_sre_subagent_design__sre_artifacts_learnings.py`
  - `test_spec_sre_subagent_design__sre_intent_routing.py`
  - `test_spec_sre_subagent_design__sre_orchestrator_integration.py`
  - `test_spec_sre_subagent_design__sre_pipeline.py`
  - `test_spec_sre_subagent_design__sre_role_definition.py`
  - `test_spec_sre_subagent_design__sre_security_boundary.py`
  - `test_spec_auto_metric_degradation_verify_pass_rate_20260521__post_implement_lint_autofix.py`
  - `test_spec_auto_metric_degradation_verify_pass_rate_20260521__verify_failure_classification.py`
  - `test_spec_auto_metric_degradation_verify_pass_rate_20260521__verify_failure_observability.py`
  - `test_spec_auto_metric_degradation_verify_pass_rate_20260521__verify_rate_metric_script.py`
  - `test_spec_push_local_commits_to_remote__push_sync.py`
  - `test_spec_enable_sub_agent_gates__pipeline_gates_config.py`
- [ ] 3. 删除旧 proposal的 test_spec_* 文件及通用 spec 基础设施测试（预估复杂度：低, 预估 token：~1200 / 无历史参考）
  - `test_spec_fix_learnings_noise_and_inject__cleanup.py`
  - `test_spec_fix_learnings_noise_and_inject__filter_and_inject.py`
  - `test_spec_fix_learnings_noise_and_inject__inject_enrich.py`
  - `test_spec_fix_learnings_noise_and_inject__inject_implement.py`
  - `test_spec_fix_learnings_noise_and_inject__search.py`
  - `test_spec_parser.py` ⚠️ 可能是 spec parser 基础设施测试而非 proposal 测试
  - `test_spec_pytest_check.py` ⚠️ 可能是 pytest check 基础设施测试而非 proposal 测试
- [ ] 4. 验证剩余测试全部通过（预估复杂度：低, 预估 token：~1000 / 无历史参考）
  - 运行 `pytest tests/ -x` 确认无回归

## 边界

### IN scope
- 删除 `tests/test_spec_*` 全部 26 个文件
- 验证删除后 `pytest tests/ -x` 通过

### OUT of scope
- 修改任何源代码（`*.py` 非 tests 目录）
- 修改 `conftest_zsiga.py` 或任何非 `test_spec_*` 测试文件
- 清理其他目录下的陈旧文件
- 修改 CI/CD 配置

### 依赖的外部条件
- 删除文件后剩余测试不依赖被删文件中的 fixture 或 conftest 定义
- `pytest tests/ -x` 在当前环境下可以正常运行（需测试基础设施完整）

## 目标

### 成功标准
1. `tests/` 目录中不存在任何 `test_spec_*` 文件（`ls tests/test_spec_*` 返回空）
2. `conftest_zsiga.py` 及所有非 `test_spec_*` 测试文件保持不变
3. `pytest tests/ -x` 全部通过，无失败用例

### 验收方式
- `find tests/ -name 'test_spec_*' | wc -l` 输出 0
- `git diff --name-only` 仅包含 `tests/test_spec_*.py` 文件（全部为 delete 操作）
- `pytest tests/ -x` exit code 为 0

## 约束

### 不能修改的文件
- `tests/conftest_zsiga.py`
- 所有 `tests/test_*.py` 中非 `test_spec_*` 开头的文件
- 项目根目录下所有源代码和配置文件

### 项目部署分支
- 未指定（由主分支策略决定）

### 已知风险
- `test_spec_parser.py` 和 `test_spec_pytest_check.py` 可能测试的是 spec 基础设施功能（spec parser / pytest checker），而非特定 proposal 的验证测试。删除前应确认这两个文件是否被其他测试间接依赖，或者是否确实属于陈旧 proposal
- 被删文件中若定义了共享 fixture，可能导致剩余测试因缺少 fixture 而失败。需在验收阶段通过 `pytest tests/ -x` 捕获

### 预估 token 消耗
- prompt: ~2000
- completion: ~1000
- 数据来源: 无历史参考
