# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（496 行, 4 函数, 13 类）添加单元测试覆盖。当前缺少 `tests/test_config.py` 文件，被视为潜在风险点。要求覆盖全部 4 个公开函数，优先覆盖高复杂度函数 `validate_config`（CC=17）。

### 拆解后的子任务
- [ ] 1. 创建 `tests/test_config.py`，编写 `_find_config()` 测试（覆盖：配置文件存在/不存在、多路径搜索、路径优先级）(预估复杂度：低, 预估 token：~2000)
- [ ] 2. 编写 `_resolve_env_vars(value)` 测试（覆盖：无环境变量字符串、含 `${VAR}` 替换、嵌套变量、未定义变量回退）(预估复杂度：低, 预估 token：~1500)
- [ ] 3. 编写 `validate_config(config)` 测试（覆盖：合法配置通过、缺少必填字段、类型错误、LLM 配置验证、SSH 配置验证、边界值；CC=17 需充分分支覆盖）(预估复杂度：高, 预估 token：~4000)
- [ ] 4. 编写 `load_config(path)` 测试（覆盖：正常加载流程、文件不存在、YAML 解析错误、空文件、加载后自动校验、集成路径；~160 行大函数需 mock 文件 I/O）(预估复杂度：中, 预估 token：~3500)
- [ ] 5. 编写核心类构造/行为测试（`ValidationResult`、`ConfigValidationError`、`SSHConfig`、`TargetConfig`、`LLMConfig` 等关键类的基础验证）(预估复杂度：低, 预估 token：~2000)

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含对 `zsiga/config.py` 全部 4 个公开函数和关键类的单元测试
- 使用 mock 隔离外部依赖（文件 I/O、环境变量、subprocess）
- 优先覆盖 `validate_config`（CC=17）的分支路径
- 确保每个测试可独立运行，不依赖运行时环境

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改或迁移已有的测试文件（见下方已知风险）
- 不修改 `conftest.py` 或测试基础设施
- 不涉及其他模块的测试

### 依赖的外部条件
- `zsiga/config.py` 的公开 API 签名保持当前状态不变
- `pytest` 测试框架可用（项目已有 `tests/conftest_zsiga.py`）
- `unittest.mock` 可用（标准库）

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含至少 5 个 `def test_` 函数
2. 测试覆盖 `_find_config`、`_resolve_env_vars`、`validate_config`、`load_config` 四个公开函数
3. `validate_config` 测试覆盖主要分支（合法配置、缺少字段、类型错误至少各 1 个 case）
4. `python -m pytest tests/test_config.py` 退出码 0
5. `python -m ruff check tests/test_config.py` 无 lint 错误

### 验收方式
- BAC-01: `test -f tests/test_config.py`
- BAC-02: `grep -c 'def test_' tests/test_config.py` ≥ 5
- BAC-03: `grep -q 'test_validate_config' tests/test_config.py`
- BAC-04: `python -m pytest tests/test_config.py` 退出码 0
- BAC-05: `python -m ruff check tests/test_config.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析，不做任何修改）
- 所有已有的 `tests/test_config_*.py` 文件
- `tests/conftest_zsiga.py`
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- 当前工作分支（由 daemon 或 CLI 管理）

### 已知风险
- **已有覆盖冲突**：`zsiga/config.py` 已有 3 个测试文件（`tests/test_config_validation.py` ~39 tests, `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` ~8 tests, `tests/test_spec_evo_improvement_20260527__config_load_robustness.py` ~5 tests），共约 52 个测试。新建 `tests/test_config.py` 可能产生重复测试。建议在实施前确认已有覆盖范围，仅补充缺失场景，避免与已有测试重复。
- **高复杂度函数**：`validate_config`（CC=17, 50 行）需要充分分支覆盖，mock 策略需仔细设计
- **`load_config` 集成性**：160 行大函数涉及文件读取、YAML 解析、环境变量替换、校验串联，需多层 mock

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类任务无成功记录）
