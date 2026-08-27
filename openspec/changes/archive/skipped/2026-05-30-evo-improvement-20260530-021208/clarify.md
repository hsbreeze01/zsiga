# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为无测试模块 `zsiga/config.py`（548 行, 7 函数, 13 类）添加单元测试覆盖，新建 `tests/test_config.py`，不修改源码。

**已有覆盖分析**：`tests/test_config_validation.py`（426 行）已覆盖 `validate_config()` 和 `load_config()` 的部分场景（ValidationResult、合法配置、LLM 字段缺失、温度警告、max_tokens 警告、target 校验、pipeline 警告、LLMFastConfig 等）。本次需覆盖的是**尚未测试的函数**。

### 拆解后的子任务

- [ ] 1. **纯函数测试**：覆盖 `_find_config()`（配置文件搜索逻辑：当前目录 → `~/.zsiga/`）、`_resolve_env_vars()`（递归 `${ENV_VAR}` 环境变量插值）、`_runtime_state_path()`（运行时状态路径计算） (预估复杂度：低, 预估 token：~3000)
- [ ] 2. **运行时状态 I/O 测试**：覆盖 `load_runtime_state()` 和 `save_runtime_state(state)`，使用 tmp_path mock 隔离文件系统，测试正常读写、文件不存在、空内容等边界情况 (预估复杂度：低, 预估 token：~3000)
- [ ] 3. **数据类构造与默认值测试**：覆盖 `SSHConfig`、`TargetConfig`、`LLMConfig`、`CompactionConfig`、`PipelineConfig`、`IntakeConfig`、`SafetyConfig`、`GithubConfig`、`ZsigaConfig`、`LoggingConfig` 等类的构造参数和默认值 (预估复杂度：中, 预估 token：~4000)

## 边界

### IN scope
- 新建 `tests/test_config.py`
- 覆盖 `_find_config()`、`_resolve_env_vars()`、`_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state()` 等 5 个未覆盖函数
- 覆盖数据类的构造与默认值（补充 `test_config_validation.py` 未覆盖的类构造场景）
- BAC 要求的 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数必须存在

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有的 `tests/test_config_validation.py`
- 不覆盖 `load_config()` 的完整路径（已在 `test_config_validation.py` 的 `TestLoadConfigIntegration` 中部分覆盖）
- 不覆盖 `validate_config()` 的完整路径（已在 `test_config_validation.py` 中大量覆盖）

### 依赖的外部条件
- `zsiga/config.py` 中函数签名和类接口保持稳定
- pytest 可正常发现并运行 `tests/test_config.py`

## 目标

### 成功标准
1. `tests/test_config.py` 存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数
2. 文件中至少 3 个 `def test_` 函数
3. `python -m pytest tests/test_config.py` 退出码 0
4. 测试覆盖 5 个未覆盖函数（`_find_config`、`_resolve_env_vars`、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state`）

### 验收方式
- 检查 `tests/test_config.py` 文件存在
- grep 确认三个指定测试函数名存在
- 统计 `def test_` 函数数量 ≥ 3
- 执行 `python -m pytest tests/test_config.py -v` 确认退出码 0

## 约束

### 不能修改的文件
- `zsiga/config.py`
- `tests/test_config_validation.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- `deploy`

### 已知风险
- **已有测试重叠**：`tests/test_config_validation.py` 已包含 `TestValidationResult`、`TestValidConfig`、`TestLLMFastConfig` 等类测试，新文件需避免重复覆盖相同场景
- **`validate_config` CC=18**：高复杂度函数已在 `test_config_validation.py` 中有覆盖，BAC 要求 `test_validate_config` 存在但可简化为集成验证而非重复全覆盖
- **proposal 迭代历史**：`add-tests-config` 已有 22 次迭代尝试均未交付，需确保本次实现精简可验证

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类测试文件编写估算）
