# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数，优先覆盖高复杂度函数 `validate_config`（CC=18）。使用 mock 隔离外部依赖，确保测试可独立运行。

### 拆解后的子任务
- [ ] 1. 环境变量解析与配置文件查找测试 (`_resolve_env_vars`, `_find_config`) — 覆盖 env var 替换的各种分支（字符串/字典/列表/嵌套结构、存在/缺失、非字符串透传）及配置文件查找路径（当前目录、home 目录、FileNotFound）。(预估复杂度：低, 预估 token：~4000 / 无历史参考)
- [ ] 2. 配置校验测试 (`validate_config`) — 覆盖 CC=18 的高复杂度校验函数，包括合法配置、缺失 LLM 字段、temperature/maxTokens 警告、target 校验、pipeline 警告等主要分支路径。(预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 3. 配置加载集成测试 (`load_config`) — 覆盖 167 行的加载函数，mock YAML 文件读取，测试 SSH target 解析、pipeline 覆盖、compaction 覆盖、env var 替换、github/logging/safety/intake 各段配置解析。(预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 4. 运行时状态与数据类测试 (`_runtime_state_path`, `load_runtime_state`, `save_runtime_state`, 各 dataclass 构造) — 覆盖运行时状态路径生成、读写流程、以及 SSHConfig/TargetConfig/LLMConfig/LLMFastConfig/CompactionConfig/PipelineConfig/IntakeConfig/SafetyConfig/GithubConfig/LoggingConfig/ZsigaConfig 等数据类默认值与构造。(预估复杂度：低, 预估 token：~4000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含针对 `zsiga/config.py` 公开函数的单元测试
- 测试 `_find_config`、`_resolve_env_vars`、`validate_config`、`load_config`、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state`
- 测试各 dataclass 的构造与默认值
- 使用 mock/fixture 隔离文件 I/O 和环境变量依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件（`tests/test_config_validation.py` 等）
- 不修改 `pyproject.toml`、`requirements.txt` 或其他项目配置

### 依赖的外部条件
- **已有测试覆盖重叠**：`tests/test_config_validation.py`（~426 行）已覆盖 `validate_config`、`load_config`（集成路径）、`ConfigValidationError`、`LLMFastConfig`；`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` 已覆盖 `_find_config`、`_resolve_env_vars`；`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` 已覆盖加载健壮性。新测试文件需避免与这些文件产生逻辑重复，聚焦增量覆盖。
- `zsiga/config.py` 模块可正常 import，无外部网络依赖
- pytest 框架可用，项目已有 `tests/conftest_zsiga.py` 提供公共 fixture

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 文件中包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
3. `python -m pytest tests/test_config.py` 退出码为 0（所有测试通过）
4. `python -m ruff check tests/test_config.py` 无 lint 错误
5. 新测试不与已有 `tests/test_config_validation.py` 等文件产生 import 冲突或 fixture 冲突

### 验收方式
- 文件存在性检查：`test -f tests/test_config.py`
- 符号存在性检查：`grep -c 'def test_' tests/test_config.py` ≥ 3
- BAC 符号检查：`grep 'def test__find_config\|def test__resolve_env_vars\|def test_validate_config' tests/test_config.py`
- 测试通过：`python -m pytest tests/test_config.py -v` 退出码 0
- Lint 通过：`python -m ruff check tests/test_config.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/config.py` — 仅读取分析
- `tests/test_config_validation.py` — 已有 426 行验证/加载测试
- `tests/test_config_diff.py` — 已有配置差异测试
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` — 已有 `_find_config`/`_resolve_env_vars` 测试
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` — 已有加载健壮性测试
- `pyproject.toml`、`requirements.txt`、`zsiga.yaml`

### 项目部署分支
main

### 已知风险
- **测试覆盖重叠（高）**：`tests/test_config_validation.py` 已包含 ~30 个测试覆盖 `validate_config` 和 `load_config` 的主要路径，`test_spec_evo_...__config_unit_coverage.py` 已覆盖 `_find_config` 和 `_resolve_env_vars`。新文件中若重复覆盖相同路径，将增加维护负担而非测试价值。建议新文件聚焦**增量覆盖**：dataclass 默认值/构造、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state` 等尚未被直接测试的函数。
- **空转循环（高）**：此 proposal 已在 archive 中出现 22+ 次（均 skipped/rejected），属于自演进引擎因静态分析只匹配 `test_config.py` 文件名而忽略已有 `test_config_validation.py` 的循环提案。本次 clarify 已标注重叠范围以降低风险。
- **proposal 前提偏差（中）**：proposal 声称模块"缺少测试文件"，但已有 4+ 个测试文件直接覆盖该模块。执行时应以增量价值为导向，而非按 proposal 原文创建重复测试。

### 预估 token 消耗
- prompt: ~8000（含 context + config.py 源码参考 + 已有测试文件参考）
- completion: ~6000（测试文件生成 + mock/fixture 编写 + 调试循环）
- 数据来源: 无历史参考（同类 proposal 全部被 skip，无成功执行数据）
