# clarify.md — test-layer0-binary-verification

## 需求拆解

### 原始需求
为 commit 14b3111 引入的 Layer 0 确定性二进制验证体系编写完整的测试套件，覆盖 verify_layer0.py 的所有检查函数、verifier.py 的 Layer 0 集成、learning 格式升级（case/why/rule）、以及 context.py 消费端的新逻辑。不修改任何生产代码，仅新增 4 个测试文件。

### 拆解后的子任务

- [ ] 1. **test_verify_layer0.py — 核心数据结构与 spec 覆盖检查** (预估复杂度：中, 预估 token：~6000)
  - 文件范围：`tests/test_verify_layer0.py`（新建）
  - 内容：Layer0Check/Layer0Result 数据结构验证、check_spec_file_coverage pass/fail、check_tasks_completion pass/fail/empty、check_testable_not_all_false pass/fail、check_no_syntax_error pass/fail、check_spec_scenario_coverage pass/fail
  - 测试编号：#1–#13（共 13 个用例）

- [ ] 2. **test_verify_layer0.py — BAC 解析与端到端检查** (预估复杂度：中, 预估 token：~5000)
  - 文件范围：`tests/test_verify_layer0.py`（同一文件，追加）
  - 内容：check_bac_exists pass/fail、check_bac_reference pass、check_bac_testable_count pass/fail、run_layer0_checks 全通过/部分失败
  - 测试编号：#14–#20（共 7 个用例）

- [ ] 3. **test_verifier_layer0_integration.py — verifier Layer 0 集成** (预估复杂度：低, 预估 token：~3000)
  - 文件范围：`tests/test_verifier_layer0_integration.py`（新建）
  - 内容：verify() 在 Layer 0 FAIL 时返回 None + 写 FAIL verify.md、Layer 0 PASS 时继续 Layer 1
  - 测试编号：#21–#22（共 2 个用例）

- [ ] 4. **test_learning_format.py — learning 格式升级** (预估复杂度：低, 预估 token：~4000)
  - 文件范围：`tests/test_learning_format.py`（新建）
  - 内容：record_lesson 带 case/why/rule、record_outcome 带 case/why/rule、load_recent_lessons [RULE] 优先逻辑
  - 测试编号：#23–#25（共 3 个用例）

- [ ] 5. **test_steward_scoring.py — Steward 6 维度评分** (预估复杂度：低, 预估 token：~3000)
  - 文件范围：`tests/test_steward_scoring.py`（新建）
  - 内容：验证 _STEWARD_PROMPT 含 6 维度与 /12 总分、_parse_verdict 解析 12 分制、向后兼容 10 分制、默认阈值配置
  - 测试编号：#26–#29（共 4 个用例）

## 边界

### IN scope
- 新建 `tests/test_verify_layer0.py`（20 个测试用例，覆盖 verify_layer0.py 全部检查函数）
- 新建 `tests/test_verifier_layer0_integration.py`（2 个测试用例，覆盖 verifier.py Layer 0 集成）
- 新建 `tests/test_learning_format.py`（3 个测试用例，覆盖 learn.py record_lesson/record_outcome 的 case/why/rule 参数及 context.py [RULE] 优先逻辑）
- 新建 `tests/test_steward_scoring.py`（4 个测试用例，覆盖 roles.py 6 维度评分和 proposal_gate.py /12 解析）

### OUT of scope
- 修改 `verify_layer0.py`、`verifier.py`、`learn.py`、`context.py`、`roles.py`、`config.py` 等任何生产代码
- 修改现有测试文件
- 添加新的 pytest 插件或 conftest fixture
- 修改 `pyproject.toml` 或 `requirements.txt`

### 依赖的外部条件
- `zsiga/pipeline/verify_layer0.py` 存在且导出 `Layer0Check`、`Layer0Result`、`run_layer0_checks` 及各 `check_*` 函数
- `zsiga/pipeline/verifier.py` 的 `verify()` 函数接受 Layer 0 前置调用逻辑
- `zsiga/pipeline/learn.py` 的 `record_lesson`/`record_outcome` 接受 `case`/`why`/`rule` 关键字参数
- `zsiga/pipeline/context.py` 的 `load_recent_lessons` 实现 `[RULE]` 优先格式化
- `zsiga/pipeline/roles.py` 的 `_STEWARD_PROMPT` 包含 6 维度评分模板（含"验收可测性"，总分 /12）
- `zsiga/pipeline/proposal_gate.py` 的 `_parse_verdict` 支持 /12 分制解析
- `zsiga/config.py` 的 `PipelineConfig` 含 `proposal_gate_score_accept=10`、`proposal_gate_score_pushback=6` 默认值

## 目标

### 成功标准
1. 4 个测试文件全部存在且共含 29 个测试函数
2. `pytest tests/test_verify_layer0.py tests/test_verifier_layer0_integration.py tests/test_learning_format.py tests/test_steward_scoring_scoring.py` 退出码 0，全部通过
3. `ruff check` 对新文件无报错
4. 所有测试使用 mock/fixture 隔离，不依赖外部服务（LLM、网络、文件系统以外的 I/O）
5. 15 条 BAC 验收项全部可由代码结构验证满足

### 验收方式
- `pytest` 执行 4 个测试文件，exit code 0
- `ruff check tests/test_verify_layer0.py tests/test_verifier_layer0_integration.py tests/test_learning_format.py tests/test_steward_scoring.py` 无输出
- `grep -c "def test_" tests/test_verify_layer0.py` 输出 20
- `grep -c "def test_" tests/test_verifier_layer0_integration.py` 输出 2
- `grep -c "def test_" tests/test_learning_format.py` 输出 3
- `grep -c "def test_" tests/test_steward_scoring.py` 输出 4

## 约束

### 不能修改的文件
- `zsiga/pipeline/verify_layer0.py`
- `zsiga/pipeline/verifier.py`
- `zsiga/pipeline/learn.py`
- `zsiga/pipeline/context.py`
- `zsiga/pipeline/roles.py`
- `zsiga/pipeline/proposal_gate.py`
- `zsiga/config.py`
- `tests/conftest_zsiga.py` 及所有现有 `tests/test_*.py` 文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- main

### 已知风险
- **生产模块接口不稳定**：proposal 描述的 verify_layer0.py 是 ~700 行新模块，其公开接口（函数签名、类结构）可能已在 commit 14b3111 之后再次变更。若实际接口与 proposal 描述不符，测试需适配实际签名而非 proposal 描述。
- **learnings.jsonl 写入副作用**：test_learning_format 测试 record_lesson/record_outcome 会写入 learnings.jsonl，需确保测试后清理或使用 tmp_path 隔离，避免污染生产数据。
- **BAC 解析器依赖 proposal.md 格式**：`[BAC-NN]` 标记的解析逻辑可能对格式敏感，测试需构造精确的 proposal.md 片段。
- **历史教训 — verify false positive**：`pipeline.verify.false_positive` 教训指出 verify 曾只检查 4 个 spec 中的 1 个就声明 PASS。本测试套件需确保 run_layer0_checks 的 spec 覆盖检查确实遍历所有 spec 文件，而非仅首个。

### 预估 token 消耗
- prompt: ~18000（读取 4 个生产模块源码作为测试编写参考 + proposal 上下文）
- completion: ~12000（生成 4 个测试文件，约 29 个测试函数 + fixture）
- 数据来源: 无历史参考（同类任务无成功先例，按测试代码行数 × 3 token/行估算）
