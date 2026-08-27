# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为模块 `zsiga/config.py`（519 行, 4 函数, 13 类）创建单元测试文件 `tests/test_config.py`，覆盖公开函数 `_find_config`、`_resolve_env_vars`、`validate_config`、`load_config`，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 拆解后的子任务

- [ ] 1. **config 模块工具函数测试** — 覆盖 `_find_config()` 和 `_resolve_env_vars(value)` 两个内部函数。`_find_config` 需测试当前目录找到 / 未找到 / 回退 `~/.zsiga/zsiga.yaml` 等分支；`_resolve_env_vars` 需测试 `${VAR}` 解析、嵌套变量、无匹配环境变量、非字符串输入等场景。（预估复杂度：低, 预估 token：~3000）
- [ ] 2. **validate_config 函数测试** — 覆盖 `validate_config(config)` 的核心验证逻辑（CC=18，54 行），需构造合法 config / 缺失必填字段 / 类型错误 / 多错误聚合 / warnings 生成等场景，返回 `ValidationResult` 的 `valid` 属性与 `errors`/`warnings` 列表断言。（预估复杂度：中, 预估 token：~5000）
- [ ] 3. **load_config 集成测试（mock 隔离）** — 覆盖 `load_config(path)` 的主流程（167 行），使用 `monkeypatch` / `tmp_path` 隔离文件 I/O，测试：正常加载、文件不存在、YAML 解析失败、验证失败时抛 `ConfigValidationError`、环境变量注入链路等。（预估复杂度：中, 预估 token：~5000）

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含至少 3 个 `def test_` 函数
- 覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 的单元测试
- 覆盖 `load_config` 的 mock 隔离测试
- 使用 pytest 框架（monkeypatch、tmp_path、fixture）

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改任何现有测试文件
- 不测试 config.py 中的 dataclass 定义（`LLMConfig`、`TargetConfig`、`SSHConfig` 等 13 个类）——除非验证函数内部逻辑需要构造它们
- 不修改 conftest 或 pytest 配置

### 依赖的外部条件
- `zsiga/config.py` 的公开 API 稳定（函数签名不变）
- 现有 pytest 基础设施正常（`tests/conftest_zsiga.py` 可用）
- `pyyaml` 已安装（`load_config` 内部依赖）

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在
2. 文件中包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
3. 文件中包含至少 3 个 `def test_` 函数
4. `python -m pytest tests/test_config.py` 退出码为 0（全部通过）
5. 测试不依赖运行时环境（无真实 LLM 调用、无真实文件系统写入、无网络请求）

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 计数 ≥ 3
- `grep 'def test__find_config\|def test__resolve_env_vars\|def test_validate_config' tests/test_config.py` 确认三个目标函数存在
- `python -m pytest tests/test_config.py -v` 退出码 0，无 FAIL/ERROR
- `ruff check tests/test_config.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py` — 仅读取分析，不做任何修改
- `tests/conftest_zsiga.py` — 不修改共享 fixture
- 所有其他现有测试文件

### 项目部署分支
- `zsiga` target 的 `deploy_branch`（由 `zsiga.yaml` 中 targets.zsiga-self 配置决定）

### 已知风险
- **已有测试覆盖冲突**：`tests/test_config_validation.py`（~39 tests）已全面覆盖 `validate_config`；`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（8 tests）已覆盖 `_find_config` 和 `_resolve_env_vars`；`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（5 tests）已覆盖 `load_config`。新建 `test_config.py` 可能与已有测试产生重复，但不影响功能正确性。
- **load_config 复杂度高**（167 行）：内部调用 `_find_config`、`_resolve_env_vars`、`validate_config`，且涉及 YAML 文件读取，mock 隔离需覆盖多层调用链
- **validate_config CC=18**：分支较多，需仔细构造测试用例覆盖主要路径

### 预估 token 消耗
- prompt: ~6000（读取 config.py 分析接口 + 测试上下文）
- completion: ~5000（生成测试代码）
- 数据来源: 无历史参考（同类 proposal 多次被 PUSHBACK，无成功执行记录可参考）
