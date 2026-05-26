# test-layer0-binary-verification

## Summary
为 commit 14b3111 引入的 Layer 0 确定性二进制验证体系编写完整的测试套件，覆盖 verify_layer0.py 的所有检查函数、verifier.py 的 Layer 0 集成、learning 格式升级（case/why/rule）、以及 context.py 消费端的新逻辑。

## Problem
commit 14b3111 做了大量修改但没有任何测试覆盖：
1. verify_layer0.py 是全新模块（~700行），5 个核心检查函数 + BAC 解析器，无测试
2. verifier.py 的 verify() 新增了 Layer 0 前置调用，Layer 0 FAIL 时应直接返回 None 并写 FAIL verify.md，无测试
3. learn.py 的 record_lesson/record_outcome 新增 case/why/rule 参数，无测试
4. context.py 的 load_recent_lessons 新增 [RULE] 优先逻辑，无测试
5. roles.py Steward 评分从 5 维度/10 分改为 6 维度/12 分，无测试

## Technical Design

### File: tests/test_verify_layer0.py (新建)

测试 verify_layer0.py 的所有检查函数：

#### 1. test_layer0_check_dataclass
- 构造 Layer0Check(passed=True) 和 Layer0Check(passed=False)
- 验证 to_dict() 返回正确结构

#### 2. test_layer0_result_aggregation
- 构造 Layer0Result 包含 3 pass + 2 fail
- 验证 all_passed=False, passed_count=3, failed_checks 长度 2
- 构造全部 pass -> 验证 all_passed=True

#### 3. test_spec_file_coverage_pass
- 准备 tmp change_dir 含 specs/phase-cap-budget.md，内容含标题 Phase Token Cap TokenBudget
- mock git diff 返回含 token_budget 的变更文件
- 验证 check_spec_file_coverage 返回 passed=True

#### 4. test_spec_file_coverage_fail
- 准备 tmp change_dir 含 specs/phase-cap-config.md, specs/phase-cap-loop.md, specs/phase-cap-orchestration.md
- mock git diff 只返回 token_budget.py 变更（不包含 config/loop/orchestration）
- 验证 check_spec_file_coverage 返回 passed=False，evidence 包含未覆盖的 spec 名

#### 5. test_tasks_completion_pass
- 准备 tasks.md 内容全为 - [x]
- 验证 passed=True

#### 6. test_tasks_completion_fail
- 准备 tasks.md 含 - [ ] 未勾选项
- 验证 passed=False，evidence 包含未完成数量

#### 7. test_tasks_completion_empty
- 无 tasks.md -> 验证 passed=True（跳过）

#### 8. test_testable_not_all_false_pass
- spec 含 testable=true scenario -> passed=True

#### 9. test_testable_not_all_false_fail
- 所有 scenario 都是 testable=false（或被 demote）-> passed=False

#### 10. test_no_syntax_error_pass
- 准备合法 Python 文件 -> passed=True

#### 11. test_no_syntax_error_fail
- 准备含语法错误的 Python 文件 -> passed=False

#### 12. test_spec_scenario_coverage_pass
- spec 含 SHALL provide phase_cap -> diff 含 phase_cap -> passed=True

#### 13. test_spec_scenario_coverage_fail
- spec 含 SHALL provide get_phase_cap -> diff 不含 -> passed=False

#### 14. test_bac_exists_pass
- proposal.md 含 [BAC-01] config.py 中存在 PHASE_TOKEN_CAPS
- mock config.py 源码含 PHASE_TOKEN_CAPS -> passed=True

#### 15. test_bac_exists_fail
- proposal.md 含 [BAC-01] loop.py 中存在 handle_cap_exceeded
- mock loop.py 不含 -> passed=False

#### 16. test_bac_reference_pass
- proposal.md 含 [BAC-02] orchestrator.py 中引用了 cap_exceeded
- mock orchestrator.py 含 cap_exceeded -> passed=True

#### 17. test_bac_testable_count_pass
- proposal.md 含 [BAC-10] 至少存在 1 个 testable=true
- mock spec 含 1 个 testable=true -> passed=True

#### 18. test_bac_testable_count_fail
- proposal.md 同上，但 mock spec 全部 testable=false -> passed=False

#### 19. test_run_layer0_checks_all_pass
- mock 所有依赖使全部检查通过
- 验证 Layer0Result.all_passed=True，verify_layer0.json 被写入

#### 20. test_run_layer0_checks_partial_fail
- mock spec_file_coverage FAIL
- 验证 Layer0Result.all_passed=False，failed_checks 包含 spec_file_coverage

### File: tests/test_verifier_layer0_integration.py (新建)

测试 verifier.py 与 Layer 0 的集成：

#### 21. test_verify_returns_none_on_layer0_fail
- mock run_layer0_checks 返回 all_passed=False
- 调用 verify() -> 验证返回 None（不调用 LLM）
- 验证 verify.md 被 write_layer0_verify_md 写入，含 Verdict: FAIL

#### 22. test_verify_proceeds_to_layer1_on_layer0_pass
- mock run_layer0_checks 返回 all_passed=True
- 验证 verify() 继续执行 Layer 1 逻辑

### File: tests/test_learning_format.py (新建)

#### 23. test_record_lesson_with_case_why_rule
- 调用 record_lesson(title=test, context=ctx, takeaway=tw, case={what: something}, why=because, rule=do X)
- 读 learnings.jsonl 最后一行
- 验证 JSON 含 case、why、rule 字段
- 清理：删除写入的行

#### 24. test_record_outcome_with_case_why_rule
- 调用 record_outcome(change, proj, False, verify, case={what: w}, why=y, rule=r)
- 读 learnings.jsonl 最后一行
- 验证 JSON 含 case、why、rule 字段
- 清理

#### 25. test_load_recent_lessons_prefers_rule
- 写入两条 learning：一条有 rule，一条只有 takeaway
- 调用 load_recent_lessons()
- 验证有 rule 的条目以 [RULE] 开头
- 验证无 rule 的条目以 [pattern_key] 开头
- 清理

### File: tests/test_steward_scoring.py (新建)

#### 26. test_steward_prompt_has_6_dimensions
- 读取 roles.py 中 _STEWARD_PROMPT
- 验证包含 验收可测性
- 验证包含 总分: X/12

#### 27. test_proposal_gate_parse_verdict_12
- 调用 _parse_verdict 含 总分: 10/12
- 验证 score=10

#### 28. test_proposal_gate_parse_verdict_10_fallback
- 调用 _parse_verdict 含 总分: 7/10
- 验证 score=7（向后兼容旧格式）

#### 29. test_config_default_thresholds
- 加载 PipelineConfig 默认值
- 验证 proposal_gate_score_accept=10, proposal_gate_score_pushback=6

## Acceptance Criteria

### Binary Acceptance Checks (automated, Layer 0 verified)
- [BAC-01] tests/test_verify_layer0.py 文件存在
- [BAC-02] tests/test_verifier_layer0_integration.py 文件存在
- [BAC-03] tests/test_learning_format.py 文件存在
- [BAC-04] tests/test_steward_scoring.py 文件存在
- [BAC-05] tests/test_verify_layer0.py 中存在 test_spec_file_coverage_pass
- [BAC-06] tests/test_verify_layer0.py 中存在 test_spec_file_coverage_fail
- [BAC-07] tests/test_verify_layer0.py 中存在 test_bac_exists_pass
- [BAC-08] tests/test_verify_layer0.py 中存在 test_run_layer0_checks_all_pass
- [BAC-09] tests/test_verify_layer0.py 中存在 test_run_layer0_checks_partial_fail
- [BAC-10] tests/test_verifier_layer0_integration.py 中存在 test_verify_returns_none_on_layer0_fail
- [BAC-11] tests/test_learning_format.py 中存在 test_record_lesson_with_case_why_rule
- [BAC-12] tests/test_learning_format.py 中存在 test_load_recent_lessons_prefers_rule
- [BAC-13] tests/test_steward_scoring.py 中存在 test_steward_prompt_has_6_dimensions
- [BAC-14] 所有 spec 文件 (4个) 都有对应的代码变更
- [BAC-15] 至少存在 1 个 testable=true 的 scenario

### Behavioral Criteria (LLM-verified)
- BC-01: 所有测试用 pytest 执行通过（exit code 0）
- BC-02: 测试使用 mock/fixture 隔离，不依赖外部服务
- BC-03: ruff check 通过

## Scope
- In scope: 测试文件（4 个新 test_*.py），不修改任何生产代码
- Out of scope: 修改 verify_layer0.py、verifier.py、learn.py、context.py、roles.py、config.py

## Risk
- Impact: None — 只添加测试文件，不改动生产代码
- Reversibility: 删除 4 个测试文件即可
- Blast radius: tests/ 目录，零影响生产
