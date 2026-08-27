# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（519 行、4 函数、13 类）新建 `tests/test_config.py`，提供单元测试覆盖，重点覆盖高复杂度函数 `validate_config`（CC=18）。

### ⚠️ 前提事实核验（需求工程师标注）

**proposal 声称 config.py "缺少测试文件"，但项目已有以下测试覆盖该模块：**

| 已有测试文件 | 覆盖内容 |
|---|---|
| `tests/test_config_validation.py` | `validate_config` 全面测试、`ValidationResult`、`ConfigValidationError`、`load_config` 集成 |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | `_find_config`、`_resolve_env_vars` 单元测试 |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | `load_config` 鲁棒性测试 |
| `tests/test_target_manifest.py` | `load_config` 相关场景 |
| `tests/test_venv_usage.py` | `load_config` 相关场景 |
| `tests/test_github_issue.py` | `load_config` 相关场景 |

**BAC-02 要求的 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数已被上述文件覆盖。盲目执行将产生重复测试。**

**建议：执行者应先审计已有测试的实际覆盖缺口，只为真正未覆盖的路径编写测试。** 真正可能缺失的覆盖：`CompactionConfig`（L103）、`LoggingConfig`（L234）、`GithubConfig`（L217）、`IntakeConfig`（L200）、`SafetyConfig`（L209）等数据类的独立验证逻辑。

### 拆解后的子任务

- [ ] 1. **审计已有测试覆盖缺口** — 扫描 `tests/test_config_validation.py`、`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`、`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` 的实际覆盖范围，对照 `zsiga/config.py` 的 4 函数 + 13 类，输出 gap list (预估复杂度：中, 预估 token：~3000 / 无历史参考)
- [ ] 2. **为覆盖缺口编写测试** — 在 `tests/test_config.py` 中为审计发现的未覆盖路径编写测试，重点包括：(a) 尚未被直接测试的 dataclass 构造与默认值（CompactionConfig、LoggingConfig、GithubConfig、IntakeConfig、SafetyConfig 等），(b) `validate_config` 的高 CC 分支（如已有覆盖则跳过），(c) `load_config` 中 YAML 解析→对象组装的边界情况（如已有覆盖则跳过） (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 3. **验证测试通过** — 运行 `python -m pytest tests/test_config.py` 确认退出码 0，运行 `ruff check` 确认无 lint 问题 (预估复杂度：低, 预估 token：~1000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_config.py`
- 为 `zsiga/config.py` 中**已有测试未覆盖的路径**编写单元测试
- 重点覆盖 `validate_config`（CC=18）中未被 `test_config_validation.py` 覆盖的分支
- 覆盖未被测试的数据类（CompactionConfig、LoggingConfig、GithubConfig、IntakeConfig、SafetyConfig 等）

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件（`test_config_validation.py` 等）
- 不重复已有测试中已覆盖的场景

### 依赖的外部条件
- `zsiga/config.py` 模块结构不变（4 函数 + 13 类）
- 已有测试文件可正常 import 和运行
- pytest + ruff 基础设施可用

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 新测试覆盖了已有测试文件中**未覆盖**的 `zsiga/config.py` 路径（不与 `test_config_validation.py`、`test_spec_evo_improvement_*__config_*.py` 重复）
3. `python -m pytest tests/test_config.py` 退出码 0
4. `ruff check tests/test_config.py` 无错误

### 验收方式
- 文件存在性检查：`test -f tests/test_config.py`
- 符号存在性检查：`grep -c 'def test_' tests/test_config.py` ≥ 3
- pytest 执行：`python -m pytest tests/test_config.py -v`
- ruff 检查：`ruff check tests/test_config.py`
- 非重复性检查（人工/脚本）：新测试的测试名与 `test_config_validation.py`、`test_spec_evo_improvement_*__config_*.py` 中的测试名不重复

## 约束

### 不能修改的文件
- `zsiga/config.py`
- `tests/test_config_validation.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`
- `tests/conftest_zsiga.py`

### 项目部署分支
- main

### 已知风险
- **重复测试风险（高）**：proposal 核心前提"config.py 缺少测试"不成立，已有 3+ 专用测试文件覆盖全部 4 个公开函数。执行者必须在编写前完成覆盖缺口审计，否则将产生大量重复测试
- **auto-generated proposal 质量（中）**：此 proposal 由自演进引擎生成，静态分析只检查了单一文件名 `tests/test_config.py` 是否存在，未扫描整个 tests 目录
- **BAC 与实际需求脱节（低）**：BAC-02 要求 `test__find_config`、`test__resolve_env_vars`、`test_validate_config`，但这三个函数已被充分覆盖。执行者应以覆盖缺口为导向而非严格遵循 BAC-02 的函数名

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（同类 proposal 曾被 PUSHBACK 多次，无成功执行记录）
