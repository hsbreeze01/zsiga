# clarify.md — add-tests-config

> ⚠️ **重叠警告**：项目中已存在 `tests/test_config_validation.py`（426 行），已覆盖 `validate_config`、`load_config`、config 数据类构造、`_resolve_env_vars`、`_find_config`、`_runtime_state_path` 等。proposal 要求创建的 `tests/test_config.py` 与之存在显著重叠。以下需求拆解已标注重叠部分，执行时应以**补充未覆盖路径**为主，避免重复测试。

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行，7 函数，13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 拆解后的子任务

- [ ] 1. **config 数据类构造与默认值测试** — 覆盖 `SSHConfig`、`TargetConfig`、`LLMConfig`、`LLMFastConfig`、`CompactionConfig`、`PipelineConfig`、`IntakeConfig`、`SafetyConfig`、`GithubConfig`、`ZsigaConfig`、`LoggingConfig` 的构造及字段默认值。(预估复杂度：中, 预估 token：~4000 / 无历史参考)
  - ⚠️ `tests/test_config_validation.py` 已有 `TestSSHConfigConstruction`、`TestTargetConfigDefaults`、`TestLLMConfigDefaults` 等覆盖，执行时应查重去冗
  - 文件范围：`tests/test_config.py`（新建）

- [ ] 2. **`_resolve_env_vars` 边界与递归测试** — 覆盖嵌套 dict/list 递归解析、`$ENV_VAR` 语法变体、无匹配环境变量时的 fallback 行为。(预估复杂度：低, 预估 token：~2500 / 无历史参考)
  - ⚠️ `tests/test_config_validation.py` 已有 `TestResolveExistingEnvVar`、`TestResolveMissingEnvVar`、`TestResolveDictRecursively` 等，查重后仅补充缺失路径
  - 文件范围：`tests/test_config.py`

- [ ] 3. **`_find_config` 路径搜索测试** — 覆盖当前目录命中、`~/.zsiga/` fallback、`FileNotFoundError` 抛出。(预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - ⚠️ `tests/test_config_validation.py` 已有 `TestFindConfigInCurrentDir`、`TestFindConfigInHomeDir`、`TestFindConfigRaisesFileNotFound`
  - 文件范围：`tests/test_config.py`

- [ ] 4. **`validate_config` 高复杂度路径测试** — CC=18 的核心函数，需覆盖：LLM 字段缺失、temperature 越界、target 验证、pipeline 参数边界、SSH 配置校验、safety 字段校验、intake api_poll 模式校验等。重点补充现有测试未覆盖的分支。(预估复杂度：高, 预估 token：~5000 / 无历史参考)
  - ⚠️ 现有 `tests/test_config_validation.py` 已有大量 validate 测试，需先 grep 确认缺失分支再编写
  - 文件范围：`tests/test_config.py`

- [ ] 5. **runtime state 读写测试** — 覆盖 `_runtime_state_path`、`load_runtime_state`、`save_runtime_state` 三个函数，使用 tmp_path mock 文件系统。(预估复杂度：低, 预估 token：~2500 / 无历史参考)
  - ⚠️ `tests/test_config_validation.py` 已有 `TestRuntimeStatePathWithZsigaHome`
  - 文件范围：`tests/test_config.py`

- [ ] 6. **pytest 通过 & lint 清洁验证** — 确保 `python -m pytest tests/test_config.py` exit 0，`ruff check tests/test_config.py` 无错误。(预估复杂度：低, 预估 token：~1000 / 无历史参考)
  - 文件范围：`tests/test_config.py`

## 边界

### IN scope
- 创建 `tests/test_config.py` 文件
- 覆盖 `zsiga/config.py` 中 7 个函数的单元测试
- 覆盖 13 个类的构造与默认值测试
- 使用 mock/tmp_path 隔离文件系统和环境变量
- 确保 pytest 通过、ruff 无错误

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改现有 `tests/test_config_validation.py`
- 不修改 `pyproject.toml`、`requirements.txt` 等配置文件
- 不添加新的依赖包

### 依赖的外部条件
- Python ≥ 3.10 环境可用
- `pytest` 和 `ruff` 已安装且可执行
- `zsiga/config.py` 当前状态无 lint 错误（已确认 0 issues）

## 目标

### 成功标准
1. 文件 `tests/test_config.py` 存在且包含 ≥3 个 `def test_` 函数
2. 测试函数覆盖 proposal 要求的三个函数：`test__find_config`、`test__resolve_env_vars`、`test_validate_config`
3. `python -m pytest tests/test_config.py` 退出码为 0
4. `ruff check tests/test_config.py` 无错误
5. 新测试与现有 `tests/test_config_validation.py` 无逻辑重复

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 确认测试数量
- `python -m pytest tests/test_config.py -v` 确认全部通过
- `ruff check tests/test_config.py` 确认无 lint 错误
- 抽查与 `tests/test_config_validation.py` 的测试函数名无重复

## 约束

### 不能修改的文件
- `zsiga/config.py` — 仅读取分析
- `tests/test_config_validation.py` — 现有测试不可动
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- deploy（具体分支名需从 `zsiga.yaml` 的 `targets.zsiga.deploy_branch` 读取）

### 已知风险
- **测试重叠风险（高）**：`tests/test_config_validation.py` 已覆盖大部分目标函数，盲目创建 `tests/test_config.py` 可能产生冗余测试。执行前必须先读取现有测试，仅补充未覆盖路径。
- **自演进引擎循环风险（中）**：同类 `add-tests-*` proposal 已在 archive 中反复出现（多次 skip/reject），根本原因是引擎未检测到已有的测试文件。此 proposal 可能再次被拒。
- **`validate_config` 分支爆炸（中）**：CC=18 意味着至少 18 条独立路径，现有测试可能已覆盖大部分，需精确分析后仅补充缺失分支。
- **环境变量副作用（低）**：`_resolve_env_vars` 测试需 mock `os.environ`，需确保不污染全局环境。

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类 proposal 均未到达执行阶段）
