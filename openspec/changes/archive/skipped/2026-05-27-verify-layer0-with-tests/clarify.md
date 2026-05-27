# clarify.md — test-layer0-binary-verification

## 需求拆解

### 原始需求
为 commit 14b3111 引入的 Layer 0 确定性二进制验证体系编写完整的测试套件，覆盖 `verify_layer0.py` 的所有检查函数、`verifier.py` 的 Layer 0 集成、`learn.py` 的 learning 格式升级（case/why/rule）、`context.py` 消费端的新逻辑、以及 `roles.py` Steward 评分维度变更。共 4 个新测试文件、29 个测试用例，不修改任何生产代码。

### 拆解后的子任务

- [ ] 1. **test_verify_layer0.py — 核心检查函数测试** (预估复杂度：高, 预估 token：~18000 / 无历史参考)
  - 文件范围：`tests/test_verify_layer0.py`（新建）
  - 覆盖：Layer0Check/Layer0Result 数据结构（test 1-2）、check_spec_file_coverage（test 3-4）、check_tasks_completion（test 5-7）、check_testable_not_all_false（test 8-9）、check_no_syntax_error（test 10-11）、check_spec_scenario_coverage（test 12-13）、check_bac_exists（test 14-15）、check_bac_reference（test 16）、check_bac_testable_count（test 17-18）、run_layer0_checks 集成（test 19-20）
  - 关键依赖：`verify_layer0.py` 中的 `Layer0Check`, `Layer0Result`, `check_spec_file_coverage`, `check_tasks_completion`, `check_testable_not_all_false`, `check_no_syntax_error`, `check_spec_scenario_coverage`, `run_layer0_checks`, `write_layer0_verify_md`
  - 注意：需要大量 mock（git diff、文件系统、配置），每个检查函数至少需要 pass/fail 两组测试

- [ ] 2. **test_verifier_layer0_integration.py — verifier 集成测试** (预估复杂度：中, 预估 token：~6000 / 无历史参考)
  - 文件范围：`tests/test_verifier_layer0_integration.py`（新建）
  - 覆盖：Layer 0 FAIL 时 verify() 返回 None 并写 FAIL verify.md（test 21）、Layer 0 PASS 时继续 Layer 1（test 22）
  - 关键依赖：`verifier.py` 中的 `verify()`、`verify_layer0.py` 中的 `run_layer0_checks`、`write_layer0_verify_md`
  - 注意：仅 2 个测试，但依赖 verifier.py 的完整 mock 链

- [ ] 3. **test_learning_format.py — learning 格式升级测试** (预估复杂度：中, 预估 token：~8000 / 无历史参考)
  - 文件范围：`tests/test_learning_format.py`（新建）
  - 覆盖：record_lesson 新增 case/why/rule 字段（test 23）、record_outcome 新增 case/why/rule 字段（test 24）、load_recent_lessons [RULE] 优先逻辑（test 25）
  - 关键依赖：`learn.py` 中的 `record_lesson`、`record_outcome`；`context.py` 中的 `load_recent_lessons`；learnings.jsonl 文件 I/O
  - 注意：每个测试需要写后读再清理 learnings.jsonl，存在并发安全风险

- [ ] 4. **test_steward_scoring.py — Steward 评分维度测试** (预估复杂度：低, 预估 token：~5000 / 无历史参考)
  - 文件范围：`tests/test_steward_scoring.py`（新建）
  - 覆盖：_STEWARD_PROMPT 含 6 维度/12 分（test 26）、_parse_verdict 解析 12 分制（test 27）、向后兼容 10 分制（test 28）、PipelineConfig 默认阈值（test 29）
  - 关键依赖：`roles.py` 中的 `_STEWARD_PROMPT`、`proposal_gate.py` 中的 `_parse_verdict`、`config.py` 中的 `PipelineConfig`
  - 注意：需要确认 `_parse_verdict` 和 `PipelineConfig.proposal_gate_score_accept/pushback` 是否实际存在

## 边界

### IN scope
- 新建 `tests/test_verify_layer0.py`（20 个测试用例）
- 新建 `tests/test_verifier_layer0_integration.py`（2 个测试用例）
- 新建 `tests/test_learning_format.py`（3 个测试用例）
- 新建 `tests/test_steward_scoring.py`（4 个测试用例）
- 测试中使用的 mock/fixture 辅助代码

### OUT of scope
- 修改 `verify_layer0.py`、`verifier.py`、`learn.py`、`context.py`、`roles.py`、`config.py` 等任何生产代码
- 修改现有测试文件
- 修改 `proposal_gate.py`
- 添加新的 pip 依赖

### 依赖的外部条件
- **关键前置条件**：`verify_layer0.py` 必须存在于 `zsiga/` 目录中且导出 `Layer0Check`, `Layer0Result`, `check_spec_file_coverage`, `check_tasks_completion`, `check_testable_not_all_false`, `check_no_syntax_error`, `check_spec_scenario_coverage`, `run_layer0_checks`, `write_layer0_verify_md` 等符号
- **关键前置条件**：`verifier.py` 必须存在且导出 `verify()` 函数
- **关键前置条件**：`learn.py` 必须存在且 `record_lesson`/`record_outcome` 支持 `case`/`why`/`rule` 关键字参数
- **关键前置条件**：`context.py` 必须存在且 `load_recent_lessons` 支持 `[RULE]` 优先逻辑
- **关键前置条件**：`roles.py` 必须存在且含 `_STEWARD_PROMPT`（6 维度/12 分制）
- **关键前置条件**：`proposal_gate.py` 必须含 `_parse_verdict` 函数（支持 /12 和 /10 格式）
- **关键前置条件**：`config.py` 的 `PipelineConfig` 必须含 `proposal_gate_score_accept`/`proposal_gate_score_pushback` 字段
- commit 14b3111 已合入目标分支，所有被测代码已就位
- `pytest` 和 `ruff` 可在 venv2 环境中正常执行

## 目标

### 成功标准
1. 4 个新测试文件全部创建，包含共 29 个测试函数
2. `pytest tests/test_verify_layer0.py tests/test_verifier_layer0_integration.py tests/test_learning_format.py tests/test_steward_scoring.py` 全部通过（exit code 0）
3. `ruff check` 对新文件无 error
4. 测试通过 mock/fixture 隔离，不依赖外部服务（LLM API、网络）
5. BAC-01 至 BAC-15 全部可验证通过

### 验收方式
- `pytest` 命令行执行 4 个测试文件，exit code 0
- `ruff check tests/test_verify_layer0.py tests/test_verifier_layer0_integration.py tests/test_learning_format.py tests/test_steward_scoring.py` 无 error
- 人工确认测试文件中存在 BAC-05 至 BAC-13 要求的具体测试函数名

## 约束

### 不能修改的文件
- `zsiga/pipeline/verify_layer0.py`（如果有）
- `zsiga/pipeline/verifier.py`（如果有）
- `zsiga/pipeline/learn.py`（如果有）
- `zsiga/pipeline/context.py`（如果有）
- `zsiga/pipeline/roles.py`（如果有）
- `zsiga/config.py`（如果有）
- `zsiga/pipeline/proposal_gate.py`（如果有）
- 所有现有 `tests/test_*.py` 文件
- `requirements.txt`、`pyproject.toml`

### 项目部署分支
- 主开发分支（具体名称需确认，proposal 提及 commit 14b3111）

### 已知风险
- **🔴 被测模块可能不存在**：并行探索结果确认 `layer0` 相关代码在项目中未找到。`verify_layer0.py`、`verifier.py`、`roles.py` 等文件的存在性未经验证。如果 commit 14b3111 的变更未合入或文件位于不同路径，测试将因 ImportError 全部失败，BC-01 无法满足
- **🔴 _STEWARD_PROMPT 和 _parse_verdict 符号不确定**：历史 pushback 记录表明 `roles.py` 和 `verifier.py` 可能不存在于代码库中。test_steward_scoring.py 的 4 个测试可能全部悬空
- **🟡 learnings.jsonl 并发安全**：test 23-25 需要读写 learnings.jsonl，如果并行执行测试或 learnings.jsonl 被其他进程使用，可能导致数据污染
- **🟡 mock 复杂度高**：test_verify_layer0.py 涉及 20 个测试，需要 mock git diff、文件系统、配置对象等多个外部依赖，mock 不准确会导致误报
- **🟡 向后兼容假设**：test 28 假设 _parse_verdict 同时支持 /12 和 /10 格式，如果实际实现只支持 /12，该测试需要调整

### 预估 token 消耗
- prompt: ~22000
- completion: ~12000
- 数据来源: 无历史参考（29 个测试、4 个新文件，按每个测试平均 ~350 token completion 估算，prompt 含上下文约 550 token/测试）
