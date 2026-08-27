# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行，7 函数，13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数，优先覆盖高复杂度函数 `validate_config`（CC=18）。使用 mock 隔离外部依赖，确保每个测试可独立运行。

**重要前置事实**：项目中已存在多个测试文件覆盖 `zsiga/config.py` 的部分功能：
- `tests/test_config_validation.py` — 覆盖 `validate_config`、`load_config`、`ValidationResult`、`ConfigValidationError`、`LLMFastConfig` 等（~426 行，~30 测试）
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` — 覆盖 `_find_config`、`_resolve_env_vars`
- `tests/test_config_diff.py` — 覆盖 `config_diff.py`（关联模块）

因此本 proposal 的实际价值应为**增量补充**未覆盖的函数/类，而非从零创建测试。

### 拆解后的子任务

- [ ] 1. **为低复杂度工具函数编写增量测试** — `_find_config()`、`_resolve_env_vars()`、`_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state()` 的单元测试，覆盖边界条件（路径不存在、环境变量缺失、状态文件损坏等）(预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. **为高复杂度函数 `validate_config` 编写增量测试** — 补充现有 `test_config_validation.py` 未覆盖的分支路径（CC=18 意味着至少 18 条独立路径），包括：空 config、缺少必需字段、类型错误、嵌套结构验证等 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 3. **为配置数据类编写结构验证测试** — `SSHConfig`、`TargetConfig`、`LLMConfig`、`CompactionConfig`、`SafetyConfig`、`IntakeConfig` 等的构造和属性验证 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 4. **确认与现有测试无重复并通过全量 pytest** — 确保 `tests/test_config.py` 不与 `test_config_validation.py`、`test_spec_evo_..._config_unit_coverage.py` 产生重复断言，且 `python -m pytest tests/test_config.py` 退出码 0 (预估复杂度：低, 预估 token：~1000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_config.py`，为 `zsiga/config.py` 中的公开/私有函数编写**增量**单元测试
- 覆盖 `save_runtime_state()`、`load_runtime_state()`、`_runtime_state_path()` 等现有测试文件中未充分覆盖的函数
- 为 `validate_config`（CC=18）补充分支覆盖
- 使用 `unittest.mock` 隔离文件 I/O、环境变量、subprocess

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改现有测试文件（`test_config_validation.py`、`test_spec_evo_..._config_unit_coverage.py`）
- 不修改 `config_diff.py` 或其他关联模块
- 不涉及 dashboard、pipeline、daemon 等其他子系统

### 依赖的外部条件
- `zsiga/config.py` 当前 API 稳定，不在其他进行中的 change 中被修改
- Python ≥3.10 测试环境可用，`pytest` + `unittest.mock` 可用
- 现有测试文件中的 fixture 和 mock 模式可参考但不依赖

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 测试覆盖 `validate_config` 的关键分支路径（至少覆盖 CC > 10 的复杂度）
3. 测试覆盖 `_find_config`、`_resolve_env_vars`、`save_runtime_state`、`load_runtime_state` 等函数
4. `python -m pytest tests/test_config.py` 退出码 0，无 skip/error
5. 与现有测试文件无功能重复（不重复测试 `test_config_validation.py` 已覆盖的相同断言）
6. `ruff check tests/test_config.py` 无 lint 错误

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 确认测试函数数量 ≥ 3
- `grep -E 'test__find_config|test__resolve_env_vars|test_validate_config' tests/test_config.py` 确认关键测试函数存在
- `python -m pytest tests/test_config.py -v` 退出码 0
- `python -m ruff check tests/test_config.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/config.py`
- `tests/test_config_validation.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`
- `tests/test_config_diff.py`
- `zsiga/config_diff.py`

### 项目部署分支
- `deploy`

### 已知风险
- **重复测试风险**：`test_config_validation.py` 已有 ~30 个测试覆盖 `validate_config`、`load_config` 等核心函数，新建测试文件需明确增量价值，避免重复断言
- **Zombie proposal 历史**：此 proposal 已迭代 22+ 次均被 skip/reject，需确保此次实现有实质性增量，而非简单重复现有测试
- **`validate_config` 高复杂度**：CC=18 意味着完全覆盖所有分支需要大量测试用例，需合理控制范围，优先覆盖核心路径
- **静态分析数据可能不完整**：proposal 中"函数数: 7，类数: 13"需与实际源码交叉验证

### 预估 token 消耗
- prompt: ~5000
- completion: ~6000
- 数据来源: 无历史参考（同类 proposal 22+ 次均未进入实施阶段）
