# clarify.md — add-tests-config

## 需求拆解
### 原始需求
为无测试模块 `zsiga/config.py`（548 行, 7 函数, 13 类）新建 `tests/test_config.py`，编写单元测试覆盖公开函数与关键类，优先覆盖高复杂度函数 `validate_config`（CC=18）。不修改源码。

### 拆解后的子任务
- [ ] 1. **配置加载与发现测试** — 覆盖 `_find_config()`（配置文件搜索路径优先级）、`load_config()`（YAML 解析、环境变量插值、ZsigaConfig 数据类构建全流程）。需 mock 文件 I/O。 (预估复杂度：高, 预估 token：~8000 / 无历史参考)
- [ ] 2. **配置校验测试** — 覆盖 `validate_config()`（CC=18，54 行），包括合法配置通过、缺少必填字段、类型错误、targets 校验、agent 配置校验、safety 策略校验等分支路径。需构造多种 ValidConfig / MissingLLMFields / TemperatureWarning 等场景。 (预估复杂度：高, 预估 token：~8000 / 无历史参考)
- [ ] 3. **工具函数与运行时状态测试** — 覆盖 `_resolve_env_vars()`（`${ENV_VAR}` 解析与回退）、`_runtime_state_path()`（路径生成）、`load_runtime_state()`、`save_runtime_state()`（读写 runtime_state.yaml）。需 mock 文件系统与环境变量。 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 4. **数据类构造与属性测试** — 覆盖 `ValidationResult`、`ConfigValidationError`、`SSHConfig`、`TargetConfig`、`LLMConfig` 等数据类的 `__init__`、属性访问、默认值、`valid()` 方法。 (预估复杂度：低, 预估 token：~3000 / 无历史参考)

## 边界
### IN scope
- 新建 `tests/test_config.py`，覆盖 `zsiga/config.py` 的 7 个函数和核心数据类
- 使用 mock 隔离文件 I/O、环境变量、subprocess 等外部依赖
- 确保测试独立可运行，通过 `pytest tests/test_config.py` 退出码 0
- 通过 `ruff check tests/test_config.py` 无 lint 错误

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件（`tests/test_config_validation.py`、`tests/test_config_diff.py`）
- 不修改 `zsiga.yaml` 或其他配置文件
- 不涉及 `zsiga/config.py` 中未导出的内部实现细节（如私有辅助函数的内部逻辑）

### 依赖的外部条件
- `zsiga/config.py` 当前 API 稳定，无近期重构计划
- 已有测试基础设施：`tests/conftest_zsiga.py`、pytest 配置就绪
- `tests/test_config_validation.py` 可能已覆盖部分 `validate_config` 路径，需查阅以避免重复但允许交叉覆盖

## 目标
### 成功标准
1. `tests/test_config.py` 文件存在且包含 ≥ 3 个 `def test_` 函数
2. 测试覆盖全部 7 个公开函数：`_find_config`、`_resolve_env_vars`、`validate_config`、`load_config`、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state`
3. `validate_config`（CC=18）至少有 3 个测试用例覆盖不同分支（合法通过、缺少字段、类型错误）
4. `python -m pytest tests/test_config.py` 退出码 0
5. `ruff check tests/test_config.py` 无错误

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 计数 ≥ 3
- `python -m pytest tests/test_config.py -v` 全部 PASSED
- `ruff check tests/test_config.py` 无输出

## 约束
### 不能修改的文件
- `zsiga/config.py`（只读分析）
- 所有已有测试文件
- `zsiga.yaml`、`pyproject.toml`、`requirements.txt`
- `data/` 目录下的运行时文件

### 项目部署分支
- `main`

### 已知风险
- `tests/test_config_validation.py` 已存在，可能已覆盖 `validate_config` 部分路径，需查阅避免完全重复的测试用例
- `load_config()` 函数 167 行，内部逻辑复杂（YAML 解析 → 环境变量插值 → 配置校验 → 返回），mock 粒度需仔细设计
- `validate_config` CC=18 意味着分支覆盖需要较多测试用例，需权衡覆盖率与任务复杂度
- 自演进引擎生成的 proposal，需注意测试质量而非仅凑数量

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考（首次为 config.py 编写测试）
