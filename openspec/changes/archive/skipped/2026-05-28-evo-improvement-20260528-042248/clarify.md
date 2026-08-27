# clarify.md — add-tests-config

> ⚠️ **关键发现：核心前提存疑。** 该 proposal 声称 `zsiga/config.py` "缺少测试文件"，但项目内已有 **至少 3 个专项测试文件、52+ 个测试函数** 覆盖该模块的核心公开 API。执行前必须先确认真实覆盖缺口，否则将产生大量重复测试。

## 需求拆解

### 原始需求
为 `zsiga/config.py`（519 行, 4 函数, 13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 已有覆盖（proposal 未识别）

| 文件 | 行数 | 覆盖范围 |
|------|------|----------|
| `tests/test_config_validation.py` | ~426 | `validate_config` 全面测试、`ValidationResult`、`ConfigValidationError`、`load_config` 集成 |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | ~120 | `_find_config`、`_resolve_env_vars` 单元测试 |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | ~80 | `load_config` 鲁棒性测试 |
| `tests/test_target_manifest.py`、`test_venv_usage.py`、`test_github_issue.py` | — | `load_config` 的不同使用场景 |

### 拆解后的子任务

- [ ] 1. **覆盖缺口审计** — 分析现有测试文件，确定 `zsiga/config.py` 中哪些函数/类/分支尚无覆盖（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 2. **创建 `tests/test_config.py` 并填充缺口测试** — 仅编写覆盖审计中发现的未覆盖函数/分支的测试，避免与已有测试重复（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 3. **验收验证** — 运行 `pytest tests/test_config.py` 确认退出码 0，确认文件中至少 3 个 `def test_` 函数存在（预估复杂度：低, 预估 token：~1000 / 无历史参考）

## 边界

### IN scope
- 创建 `tests/test_config.py`（新建文件）
- 为 `zsiga/config.py` 中**尚未被现有测试覆盖**的函数/类/分支编写测试
- 优先覆盖高复杂度函数 `validate_config` 中未覆盖的分支
- 使用 mock 隔离外部依赖（文件 I/O、环境变量）

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改或删除任何现有测试文件
- 不重复已有测试用例（特别是 `_find_config`、`_resolve_env_vars`、`validate_config` 的已有覆盖）
- 不涉及 pipeline 自身代码、dashboard、daemon 等其他模块

### 依赖的外部条件
- `zsiga/config.py` 的接口不变（当前 519 行，4 函数 13 类）
- 项目 pytest 基础设施正常（`conftest_zsiga.py`、ruff 可用）
- 现有测试文件内容不被外部修改

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 文件中包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数名（注：需确认与已有测试不重复，若已有覆盖则替换为实际缺口对应的测试名）
3. `python -m pytest tests/test_config.py` 退出码 0
4. 新测试与已有测试文件（`test_config_validation.py` 等）不产生功能重复

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 确认 ≥ 3
- `python -m pytest tests/test_config.py` 退出码 0
- 人工或 AST 对比确认新测试不与 `test_config_validation.py`、`test_spec_evo_improvement_*__config_*.py` 中的测试用例语义重复

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/test_config_validation.py`（已有覆盖，不动）
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（已有覆盖，不动）
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（已有覆盖，不动）

### 项目部署分支
- feature 分支隔离策略（具体分支名由 pipeline 编排器决定）

### 已知风险
- **重复测试风险（高）** — proposal 未扫描已有测试文件，BAC-02 要求的 `test__find_config` 和 `test__resolve_env_vars` 已在 `test_spec_evo_improvement_*__config_unit_coverage.py` 中被覆盖，直接按 BAC 执行将产生重复
- **auto-generated proposal 质量风险** — 历史教训中同类 proposal（add-tests-*）多次因"核心前提虚假"被 REJECT/PUSHBACK
- **覆盖缺口可能很小** — 52+ 现有测试已覆盖 4 个公开函数和关键类，真实未覆盖部分可能仅限于部分数据类（`CompactionConfig`、`LoggingConfig`、`GithubConfig`、`IntakeConfig`、`SafetyConfig`）或边缘分支

### 预估 token 消耗
- prompt: ~6000（含覆盖审计 + 测试编写 + 验证）
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 均未执行成功）
