# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（519 行）添加测试文件 `tests/test_config.py`，覆盖公开函数 `_find_config()`、`_resolve_env_vars()`、`validate_config()`，确保 pytest 通过。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_config.py` 并编写 `_find_config` 测试（预估复杂度：低, 预估 token：~1500）
  - 文件范围：`tests/test_config.py`（新建）
  - 覆盖：路径查找逻辑（默认路径、自定义路径、文件不存在场景）
  - ⚠️ 注意：`test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` 已有 `_find_config` 测试，需避免重复或明确增量价值

- [ ] 2. 编写 `_resolve_env_vars` 测试（预估复杂度：低, 预估 token：~1500）
  - 文件范围：`tests/test_config.py`
  - 覆盖：环境变量替换（`${VAR}` 模式、嵌套变量、无环境变量场景、非字符串输入）
  - ⚠️ 注意：同上文件已有 `_resolve_env_vars` 测试

- [ ] 3. 编写 `validate_config` 测试（预估复杂度：高, 预估 token：~4000）
  - 文件范围：`tests/test_config.py`
  - 覆盖：CC=18 的高复杂度函数，包括合法配置、缺失字段、类型错误、结构完整性校验
  - 需要 mock 外部依赖（LLM 配置、target 配置结构）
  - ⚠️ 注意：`test_config_validation.py`（426 行）已广泛覆盖此函数

- [ ] 4. 确保全文件 pytest 退出码 0，无 lint 错误（预估复杂度：低, 预估 token：~500）
  - 运行 `python -m pytest tests/test_config.py` 确认通过
  - 运行 `ruff check tests/test_config.py` 确认无 lint 问题

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含至少 3 个 `def test_` 函数
- 覆盖 `_find_config`、`_resolve_env_vars`、`validate_config`
- 使用 mock/monkeypatch 隔离文件系统与环境变量依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件
- 不覆盖 `load_config`（167 行，scope 未要求）
- 不覆盖 13 个数据类的构造函数（scope 未要求）

### 依赖的外部条件
- `zsiga/config.py` 的公开 API 稳定（`_find_config`、`_resolve_env_vars`、`validate_config` 签名不变）
- 项目 pytest 基础设施可用（`conftest_zsiga.py` 提供的 fixture）
- 已有测试文件不与新测试冲突（同名 import 路径）

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
2. `tests/test_config.py` 中至少有 3 个 `def test_` 函数
3. `python -m pytest tests/test_config.py` 退出码 0
4. `ruff check tests/test_config.py` 无错误
5. 测试逻辑非空（每个 test_ 函数包含实质性断言，非 `pass` 占位）

### 验收方式
- `test -f tests/test_config.py` 验证文件存在
- `grep -c 'def test_' tests/test_config.py` ≥ 3
- `python -m pytest tests/test_config.py` 退出码 0
- 人工审查测试是否有实质性断言覆盖

## 约束

### 不能修改的文件
- `zsiga/config.py` — 只读取分析，不做任何修改
- `tests/test_config_validation.py` — 已有 validate_config 测试，不触碰
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` — 已有 _find_config/_resolve_env_vars 测试
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` — 已有 load_config 测试

### 项目部署分支
- main

### 已知风险
- **高重复风险**：`_find_config` 已在 `test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` 中被覆盖（2 个测试）；`_resolve_env_vars` 同文件已有 6 个测试；`validate_config` 在 `test_config_validation.py` 中有 ~20 个测试。新测试大概率与已有测试重复，不增加实质覆盖
- **同 change 已有测试文件**：文件树中已存在 `test_spec_evo_improvement_20260528_014707__config_boundary_coverage.py` 和 `test_spec_evo_improvement_20260528_014707__config_data_class_defaults.py`，说明本 change 可能已部分实施
- **BAC 质量风险**：proposal 的 BAC 只要求 3 个 test_ 函数和 pytest 退出码 0，空文件加 3 个 `def test_x(): pass` 即可满足，无法保证实质覆盖

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 多次被 REJECT/PUSHBACK，无成功执行记录）
