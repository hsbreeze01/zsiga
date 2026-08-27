# clarify.md — add-tests-config

> **⚠️ 核心前提存疑**：proposal 声称 `zsiga/config.py` 缺少测试，但项目已有 3 个测试文件共 52 个测试函数覆盖该模块全部公开 API（详见边界章节）。本需求契约如实记录 proposal 内容，同时标注已有覆盖情况，供实施者判断实际工作范围。

## 需求拆解

### 原始需求
为模块 `zsiga/config.py`（496 行, 4 函数, 13 类）新建 `tests/test_config.py`，添加单元测试覆盖。优先覆盖高复杂度函数 `validate_config`（CC=17, 50 行）。使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess），确保测试可独立运行。

### 拆解后的子任务

- [ ] 1. **已有覆盖盘点与缺口分析** — 审查 `tests/test_config_validation.py`、`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`、`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` 中已有 52 个测试对 `_find_config`、`_resolve_env_vars`、`validate_config`、`load_config` 的覆盖情况，识别真实缺口（预估复杂度：低, 预估 token：~2000）
- [ ] 2. **新建 `tests/test_config.py` 并补充差异化测试** — 仅针对已有测试文件未覆盖的分支/边界场景编写新测试，避免与现有 52 个测试重复；若盘点后发现无实质缺口，则创建包含 `conftest-level` 共享 fixture 的空壳文件以满足 BAC-01/BAC-04（预估复杂度：中, 预估 token：~5000）
- [ ] 3. **验证 `python -m pytest tests/test_config.py` 退出码 0 且无 ruff 错误**（预估复杂度：低, 预估 token：~1000）

## 边界

### IN scope
- 新建 `tests/test_config.py`
- 为 `_find_config()`、`_resolve_env_vars(value)`、`validate_config(config)`、`load_config(path)` 编写差异化单元测试
- 覆盖 `validate_config`（CC=17）的高复杂度分支
- 使用 mock 隔离文件 I/O、环境变量、LLM 配置等外部依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改 `tests/test_config_validation.py` 等已有测试文件
- 不修改 `zsiga/config_diff.py` 或其他相关模块
- 不涉及 pipeline 自身代码
- 不涉及 dashboard / metrics / daemon

### 依赖的外部条件
- **已有覆盖（关键）**：以下 3 个文件已包含 52 个测试函数覆盖 config.py 的全部 4 个公开函数：
  - `tests/test_config_validation.py`（39 个测试，覆盖 `validate_config` 含 CC=17 的全部路径）
  - `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（8 个测试，覆盖 `_find_config`、`_resolve_env_vars`、`validate_config`）
  - `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（5 个测试，覆盖 `load_config` 集成与健壮性）
- `zsiga/config.py` 源码稳定（496 行, 0 lint 问题）
- `zsiga.yaml` 配置格式作为测试 fixture 基础
- pytest + ruff 可用

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数名
2. 文件中至少 3 个 `def test_` 函数定义
3. `python -m pytest tests/test_config.py` 退出码 0
4. 新测试不与已有 52 个测试产生语义重复（即覆盖已有测试未触及的分支/边界）

### 验收方式
- `test -f tests/test_config.py` 验证文件存在
- `grep -c 'def test_' tests/test_config.py` 验证测试数量 ≥ 3
- `grep -E 'def test__find_config|def test__resolve_env_vars|def test_validate_config' tests/test_config.py` 验证目标函数名
- `python -m pytest tests/test_config.py -x --tb=short` 验证全部通过
- `ruff check tests/test_config.py` 验证无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py`
- `tests/test_config_validation.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`
- `tests/conftest_zsiga.py`
- 任何 `zsiga/` 下的源码文件

### 项目部署分支
- main（通过 `git_ops.py` 管理，非本 change 关注点）

### 已知风险
- **已有覆盖冲突**：config.py 已有 52 个测试覆盖全部公开 API，新建 `tests/test_config.py` 可能产生大量重复测试。实施者必须先盘点已有覆盖再编写，否则等于白做
- **BAC 标准过低**：AC 仅要求 ≥3 个 test_ 函数和 pytest 退出 0，最低可满足方案为 3 个 `pass` 占位函数。但结合 proposal 意图（覆盖高 CC 函数），应确保测试有实质断言
- **自演进引擎生成的 proposal 盲区**：静态分析只检查了单一文件名 `tests/test_config.py` 是否存在，未扫描整个 tests 目录寻找已有覆盖，导致核心前提"缺少测试"可能不成立
- **validate_config CC=17**：50 行内有 17 个分支，mock 策略需精确匹配 `ValidationResult`、`ConfigValidationError` 等内部类

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考（需先盘点已有覆盖再决定实际编写量，可能接近零）
