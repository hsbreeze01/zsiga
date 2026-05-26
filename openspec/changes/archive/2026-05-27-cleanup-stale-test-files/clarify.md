## 需求拆解

### 原始需求
从 tests/ 目录中删除所有属于已归档或已删除 proposal 的 test_spec_* 测试文件。这些残留文件会在每个新 proposal 的 VERIFY 阶段被 pytest 一并加载运行，造成干扰和性能浪费。

### 拆解后的子任务
- [ ] 1. 删除已归档 proposal 对应的 test_spec_* 文件 (预估复杂度：低, 预估 token：~800 / 无历史参考)
  - 涉及文件：test_spec_add_health_check_endpoint__*.py, test_spec_add_proposal_stats_to_dashboard__*.py, test_spec_add_uptime_to_status_api__*.py, test_spec_dashboard_add_feedback_loop_metrics__*.py（共 7 个文件）
- [ ] 2. 删除已删除 proposal 对应的 test_spec_* 文件 (预估复杂度：低, 预估 token：~800 / 无历史参考)
  - 涉及文件：test_spec_sre_subagent_design__*.py, test_spec_auto_metric_degradation_*__*.py, test_spec_push_local_commits_to_remote__*.py, test_spec_enable_sub_agent_gates__*.py, test_spec_fix_learnings_noise_and_inject__*.py, test_spec_unify_api_route_style__*.py（共 20 个文件）
- [ ] 3. 验证剩余测试套件完整性 (预估复杂度：低, 预估 token：~600 / 无历史参考)
  - 运行 pytest tests/ -x 确认所有非 spec 测试正常通过，无 import 残留或 fixture 依赖断裂

## 边界

### IN scope
- 删除 tests/ 目录下所有 test_spec_* 文件（共约 27 个文件）
- 验证删除后剩余测试可正常通过
- 保留 conftest_zsiga.py 及所有非 spec 测试文件不变

### OUT of scope
- 不修改任何源代码文件（skills/, site/ 等目录）
- 不修改 conftest_zsiga.py 或非 spec 测试文件
- 不清理 tests/ 以外的目录
- 不新增任何文件或功能
- 不处理 test_spec_cleanup_stale_test_files__stale_test_removal.py 的保留/删除决策（由 VERIFY 阶段自行管理）

### 依赖的外部条件
- git 历史保留所有被删除文件，可随时恢复
- 剩余测试文件的 import 路径和 fixture 不依赖任何 test_spec_* 文件

## 目标

### 成功标准
1. tests/ 目录中不存在任何 test_spec_* 文件
2. conftest_zsiga.py 及所有非 spec 测试文件（test_ast_tools.py, test_compaction.py 等 ~46 个文件）保持不变
3. `pytest tests/ -x` 执行通过，无失败用例
4. 被删除文件可通过 `git checkout` 恢复

### 验收方式
- `ls tests/test_spec_* 2>/dev/null | wc -l` 返回 0
- `git diff --stat` 仅显示 tests/ 下的文件删除（无修改）
- `pytest tests/ -x` 全部通过
- `git log --oneline -1` 提交信息清晰描述删除操作

## 约束

### 不能修改的文件
- tests/conftest_zsiga.py
- tests/test_*.py（所有非 spec 测试文件）
- skills/*
- site/*
- pyproject.toml
- requirements.txt

### 项目部署分支
main

### 已知风险
- 风险极低：删除的是已归档/已删除 proposal 的测试，对应功能已不在项目中
- 若某个 test_spec_* 文件被其他非 spec 测试 import，删除可能导致 import 错误（需验证）
- test_spec_cleanup_stale_test_files__stale_test_removal.py 是当前 proposal 自身的 VERIFY 测试，需注意其生命周期管理

### 预估 token 消耗
- prompt: ~4000
- completion: ~1500
- 数据来源: 无历史参考
