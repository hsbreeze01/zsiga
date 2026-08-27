# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（519 行，4 函数，13 类）创建 `tests/test_config.py`，覆盖公开函数 `_find_config()`、`_resolve_env_vars()`、`validate_config()`、`load_config()`，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 拆解后的子任务
- [ ] 1. 为 `_find_config()` 编写单元测试（覆盖路径查找、文件存在/不存在场景）(预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 2. 为 `_resolve_env_vars()` 编写单元测试（覆盖环境变量替换、无变量、嵌套变量等边界）(预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 3. 为 `validate_config()` 编写单元测试（CC=18，覆盖校验通过、各字段缺失/非法、ValidationResult 返回等分支）(预估复杂度：中, 预估 token：~3000 / 无历史参考)
- [ ] 4. 为 `load_config()` 编写单元测试（167 行，覆盖 YAML 加载、env 解析、与 validate 集成、异常路径）(预估复杂度：中, 预估 token：~3000 / 无历史参考)
- [ ] 5. 运行 `ruff check` + `pytest tests/test_config.py` 确保通过 (预估复杂度：低, 预估 token：~500 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含对 4 个公开函数的单元测试
- 使用 monkeypatch / mock 隔离文件 I/O 和环境变量
- 每个测试函数可独立运行

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件（`tests/test_config_validation.py`、`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`、`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`）
- 不为 13 个数据类（`SSHConfig`、`TargetConfig`、`LLMConfig` 等）单独编写构造器测试，除非其包含校验逻辑

### 依赖的外部条件
- `zsiga/config.py` 中函数签名和行号范围与 proposal 描述一致（实施时需验证）
- pytest + monkeypatch 基础设施可用（`tests/conftest_zsiga.py` 已存在）
- ⚠️ **已知冲突风险**：`tests/test_config_validation.py`（~39 个测试）已覆盖 `validate_config`；`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（~8 个测试）已覆盖 `_find_config` 和 `_resolve_env_vars`；`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（~5 个测试）已覆盖 `load_config` 健壮性。新建测试文件可能产生重复覆盖，实施前必须审计已有测试以避免冗余。

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数
2. 文件中包含至少 3 个 `def test_` 函数
3. `python -m pytest tests/test_config.py` 退出码 0
4. 新测试与已有测试文件无功能重复（实施时需校验）

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` ≥ 3
- `python -m pytest tests/test_config.py -v` 全部通过
- `ruff check tests/test_config.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析，不修改）
- 所有已有测试文件（不合并、不迁移、不重命名）

### 项目部署分支
- 未指定（需在实施时从 git 确认）

### 已知风险
- **重复测试风险（高）**：已有 3 个测试文件共 ~52 个测试覆盖 config.py 的核心函数。新建 `tests/test_config.py` 极易产生冗余测试，增加维护负担。实施前必须先分析已有覆盖范围，仅针对未覆盖的分支/场景编写新测试。
- **BAC 有效性质疑**：BAC-03 要求"至少 3 个 test_ 函数"，门槛偏低——即使只写了 3 个 trivial 测试也满足 AC，无法保证覆盖质量。
- **auto-generated proposal**：此 proposal 由自演进引擎生成，静态分析数据可能存在偏差（如行号偏移、遗漏函数等），实施时需人工校验。

### 预估 token 消耗
- prompt: ~3000
- completion: ~4000
- 数据来源: 无历史参考
