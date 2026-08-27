# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数与类，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 前置事实（需确认）
proposal 声称模块"缺少测试文件"，但项目中已存在以下相关测试：
- `tests/test_config_validation.py` — 已覆盖 `validate_config`、`load_config`、`ValidationResult`、`ConfigValidationError`、`LLMConfig` 等
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` — 已覆盖 `_find_config`、`_resolve_env_vars`
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` — 已覆盖配置加载鲁棒性

**若上述文件已充分覆盖 proposal 列出的 7 个函数和关键类，则本需求的核心前提不成立，应终止。** 以下拆解假设经确认后确实存在覆盖缺口（如 `save_runtime_state`、`load_runtime_state`、`_runtime_state_path`、`SSHConfig`、`TargetConfig` 等）。

### 拆解后的子任务

- [ ] 1. **确认覆盖缺口** — 审计 `tests/test_config_validation.py` 和 `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`，列出 `zsiga/config.py` 中尚未被直接测试的函数/类，确定新增测试的增量价值 (预估复杂度：低, 预估 token：~1500)
- [ ] 2. **配置类单元测试** — 为未覆盖的配置数据类（`SSHConfig`、`TargetConfig` 等）编写构造与字段验证测试 (预估复杂度：低, 预估 token：~2000)
- [ ] 3. **运行时状态函数测试** — 为 `_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state(state)` 编写测试，使用 tmp_path 隔离文件 I/O (预估复杂度：低, 预估 token：~2000)
- [ ] 4. **高复杂度函数补充测试**（如缺口确认） — 为 `validate_config`（CC=18）中未被 `test_config_validation.py` 覆盖的分支路径添加边界测试 (预估复杂度：中, 预估 token：~3000)
- [ ] 5. **集成验证** — 确保 `python -m pytest tests/test_config.py` 退出码 0，且不与现有测试冲突 (预估复杂度：低, 预估 token：~1000)

## 边界

### IN scope
- 为 `zsiga/config.py` 中确认未被覆盖的函数/类编写增量单元测试
- 新测试文件 `tests/test_config.py`（如确认需新建）
- 使用 mock 隔离文件 I/O 和外部依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不重构或修改现有测试文件（`test_config_validation.py` 等）
- 不修改项目配置（`pyproject.toml`、`requirements.txt`）
- 不为 venv2/ 中的第三方代码编写测试

### 依赖的外部条件
- pytest 框架已就绪（项目 100+ 测试文件确认）
- `zsiga/config.py` 源码稳定，近期无重大重构
- 需确认 `zai-sdk` 的 mock 策略（`LLMConfig` 可能引用 SDK 类型）

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 所有新增测试覆盖了此前未被直接测试的函数/类（增量价值可量化）
3. `python -m pytest tests/test_config.py` 退出码 0
4. 新增测试不与现有 `test_config_validation.py`、`test_spec_evo_...__config_unit_coverage.py` 产生重复断言
5. ruff lint 对新文件零错误

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` ≥ 3
- `python -m pytest tests/test_config.py -v` 退出码 0
- `ruff check tests/test_config.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/test_config_validation.py`（已有测试，不碰）
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（已有测试，不碰）
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（已有测试，不碰）
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
deploy

### 已知风险
- **核心前提可能不成立** — proposal 声称模块"缺少测试文件"，但已有 3 个测试文件覆盖 config.py 的多数公开 API。若审计后发现无增量覆盖缺口，此任务应终止而非创建重复测试
- **zombie proposal 历史** — 此 proposal 已被 pushback 22+ 次，需避免再次产生无价值的重复测试
- **`validate_config` 高复杂度**（CC=18）— 分支路径多，完整覆盖需大量 mock，需评估投入产出比
- **数据类测试价值低** — `SSHConfig`、`TargetConfig` 等仅为 `__init__` 赋值的数据类，直接测试价值有限

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类 proposal 历史均为 rejected/pushed back，无可参考的 completion token 记录）
