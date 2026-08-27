# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（496 行，4 函数，13 类）添加单元测试覆盖，新建 `tests/test_config.py`。

### 拆解后的子任务

- [ ] 1. **路径解析与环境变量测试** — 覆盖 `_find_config()`（候选路径搜索）和 `_resolve_env_vars(value)`（`${VAR}` 递归解析）(预估复杂度：低, 预估 token：~3000)
- [ ] 2. **配置校验逻辑测试** — 覆盖 `validate_config(config)`（CC=17，最高复杂度函数），包括合法配置通过、各类字段非法时返回对应 error/warning (预估复杂度：高, 预估 token：~6000)
- [ ] 3. **配置加载集成测试** — 覆盖 `load_config(path)`，包括正常 YAML 加载、文件不存在、YAML 格式错误、字段缺失等场景，mock 文件 I/O (预估复杂度：中, 预估 token：~5000)
- [ ] 4. **数据类与异常类测试** — 覆盖 `ValidationResult.valid` 属性、`ConfigValidationError` 异常构造、`LLMFastConfig` 等关键数据类实例化 (预估复杂度：低, 预估 token：~2000)

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含针对 `zsiga/config.py` 公开函数和关键类的单元测试
- 覆盖 `_find_config`、`_resolve_env_vars`、`validate_config`、`load_config` 四个函数
- 覆盖 `ValidationResult`、`ConfigValidationError`、`LLMFastConfig` 等关键类
- 使用 mock 隔离文件 I/O 和环境变量依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改 `zsiga.yaml` 或其他配置文件
- 不修改已有测试文件（`tests/test_config_validation.py` 等）
- 不涉及其他模块的测试

### 依赖的外部条件
- `zsiga/config.py` 当前 API 签名不变（4 函数 + 13 类的接口稳定）
- pytest 框架可用
- 项目中已存在 `tests/test_config_validation.py` 等 3 个文件，共 52 个测试函数覆盖 config 模块（**注意：需确认新建测试是否与已有覆盖重复**）

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 ≥ 3 个 `def test_` 函数
2. 测试覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 三个核心函数
3. `python -m pytest tests/test_config.py` 退出码为 0
4. 新增测试与已有 52 个测试无功能重复

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 确认 ≥ 3 个测试函数
- `grep -E 'test__find_config|test__resolve_env_vars|test_validate_config' tests/test_config.py` 确认目标函数覆盖
- `python -m pytest tests/test_config.py -v` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/test_config_validation.py`（已有测试）
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（已有测试）
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（已有测试）
- `zsiga.yaml`

### 项目部署分支
main

### 已知风险
- **已有测试覆盖冲突**：config 模块已有 3 个测试文件共 52 个测试函数，proposal 声称"缺少测试"但实际已有充分覆盖。新建 `tests/test_config.py` 可能产生重复测试，需确保新增测试覆盖已有文件未覆盖的路径
- **`validate_config` 高复杂度**：CC=17 意味着至少 17 条独立路径，完整覆盖需要大量测试用例设计
- **`load_config` 外部依赖多**：涉及 YAML 解析、环境变量、文件系统，需 mock 多层依赖

### 预估 token 消耗
- prompt: ~12000
- completion: ~6000
- 数据来源: 无历史参考（同类任务曾有 pushback 记录，因已有测试覆盖导致执行价值存疑）
