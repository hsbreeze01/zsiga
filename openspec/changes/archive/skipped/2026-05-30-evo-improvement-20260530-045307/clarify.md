# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行，7 函数，13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数与类。重点是高复杂度函数 `validate_config`（CC=18）。

### 拆解后的子任务

- [ ] 1. 配置查找与环境变量解析测试 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
  - 覆盖 `_find_config()`（当前目录/家目录查找、FileNotFound）
  - 覆盖 `_resolve_env_vars(value)`（已有/缺失环境变量、dict/list 递归、纯字符串透传、非字符串透传、嵌套结构）
  - 范围：`tests/test_config.py` 中 `test__find_config*`、`test__resolve_env_vars*` 系列函数

- [ ] 2. 配置类构造与默认值测试 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
  - 覆盖 `SSHConfig`、`TargetConfig`、`LLMConfig`、`ValidationResult`、`ConfigValidationError` 及其余 8 个 data class 的构造与属性
  - 范围：`tests/test_config.py` 中 `TestSSHConfig*`、`TestTargetConfig*`、`TestLLMConfig*` 等类

- [ ] 3. validate_config 高复杂度路径测试 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
  - 覆盖 `validate_config(config)`（CC=18）的多条分支：缺失必填字段、类型错误、边界值、合法配置
  - 覆盖 `ValidationResult` 的 valid 属性在不同场景下的值
  - 范围：`tests/test_config.py` 中 `test_validate_config*` 系列函数

- [ ] 4. load_config 集成路径与运行时状态测试 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
  - 覆盖 `load_config(path)`：SSH target、pipeline 覆盖、compaction 覆盖、环境变量替换、github/logging/safety/intake 区段
  - 覆盖 `_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state(state)`：路径生成、序列化/反序列化、round-trip
  - 使用 `tmp_path` 或 `mock` 隔离文件 I/O
  - 范围：`tests/test_config.py` 中 `test_load_config*`、`test__runtime_state_path*`、`test_load_runtime_state*`、`test_save_runtime_state*` 系列函数

## 边界

### IN scope
- 新建 `tests/test_config.py`，为 `zsiga/config.py` 中 7 个公开/私有函数和 13 个类编写单元测试
- 优先覆盖 `validate_config`（CC=18）的高复杂度分支
- 使用 mock 隔离文件 I/O 和环境变量依赖
- 确保所有测试可独立运行，`pytest tests/test_config.py` 退出码 0

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改 `tests/test_config_validation.py` 或其他已有测试文件
- 不修改 `pyproject.toml`、`requirements.txt` 等构建配置
- 不涉及其他模块的测试

### 依赖的外部条件
- `zsiga/config.py` 在目标分支上保持当前结构不变（7 函数 + 13 类）
- `pytest` 可用且项目测试基础设施正常运行
- `pyyaml` 可用（`load_config` 内部依赖）

## 目标

### 成功标准
1. `tests/test_config.py` 存在且包含至少 3 个 `def test_` 函数
2. 测试覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 三个核心函数
3. `python -m pytest tests/test_config.py` 退出码 0，无失败/错误
4. `ruff check tests/test_config.py` 无 lint 错误

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 计数 ≥ 3
- `grep -E 'test__find_config|test__resolve_env_vars|test_validate_config' tests/test_config.py` 确认三个关键测试存在
- `python -m pytest tests/test_config.py -v` 退出码 0
- `ruff check tests/test_config.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析，不修改源码）
- `pyproject.toml`
- `requirements.txt`
- 其他已有测试文件（如 `tests/test_config_validation.py`、`tests/test_config_diff.py`）

### 项目部署分支
- main

### 已知风险
- **已有测试覆盖重叠**：项目 Domain Glossary 中已存在与 `config.py` 高度相关的测试类（`TestSSHConfigConstruction`、`TestTargetConfigDefaults`、`TestLLMConfigDefaults`、`TestFindConfigInCurrentDir`、`TestLoadConfigWithSSHTarget`、`TestRuntimeStatePathWithZsigaHome` 等），这些可能分布在 `tests/test_config_validation.py` 或归档的 spec 测试文件中。新建 `tests/test_config.py` 可能与已有测试功能重叠，增加维护负担。
- **高复杂度函数测试难度**：`validate_config`（CC=18）有大量分支，需要仔细构造测试数据以覆盖所有路径，可能遗漏边界情况。
- **环境变量依赖**：`_resolve_env_vars` 和 `load_config` 依赖环境变量，需用 `monkeypatch` 或 `mock.patch` 隔离，否则测试不稳定。
- **auto-generated proposal 风险**：此 proposal 由自演进引擎生成，历史上同类"补测试" proposal 有被 skip/reject 的记录（如 `add-tests-runner` × 26+ 次），需确认本次不重复已有覆盖。

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（基于模块复杂度估算：548 行源码，4 个测试模块分组）
