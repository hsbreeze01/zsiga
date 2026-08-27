## 需求拆解

### 原始需求
Proposal 要求为 `zsiga/config.py`（548 行，7 函数，13 类）新建 `tests/test_config.py` 单元测试文件，覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 等公开函数。

### 前提校验结果：❌ 核心前提虚假

**此 proposal 的核心前提——"`zsiga/config.py` 缺少测试"——与事实不符。** 该模块已有充分的测试覆盖：

| 已有测试文件 | 测试数 | 覆盖范围 |
|---|---|---|
| `tests/test_config_validation.py` | 39 | `validate_config` 全分支（CC=18）、所有 data class、`load_config` 集成 |
| `tests/test_config_diff.py` | 11 | config_diff 模块（config 下游消费者） |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | 8 | `_find_config()`、`_resolve_env_vars()` |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | 5 | `load_config` 异常路径 |

**总计 63+ 个测试函数已覆盖 config.py 的全部 7 个函数和 13 个类。**

### 僵尸提案循环证据
- 此 proposal 已被自演进引擎生成 **52+ 次**，全部 archived/skipped，0 次成功交付
- 根因：引擎在 `zsiga/intake/evolution.py` 中使用 `os.path.basename()` 提取模块名 `config`，仅查找 `tests/test_config.py` 这个精确文件名，无法发现 `test_config_validation.py` 等变体命名
- 创建 `tests/test_config.py` 只会制造第二个冗余测试文件，不解决根因

### 拆解后的子任务

> ⚠️ 以下任务按 proposal 原始意图列出，但每个任务均标注了与已有覆盖的冲突。

- [ ] 1. 创建 `tests/test_config.py` 并编写 `_find_config()` 测试 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - ⚠️ 冲突：`test_spec_...__config_unit_coverage.py` 已有 2 个 `_find_config` 测试（当前目录命中、上级目录命中、FileNotFound）
- [ ] 2. 编写 `_resolve_env_vars()` 测试 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - ⚠️ 冲突：`test_spec_...__config_unit_coverage.py` 已有 3 个 `_resolve_env_vars` 测试（existing env、missing env、nested structure）
- [ ] 3. 编写 `validate_config()` 测试（高 CC=18） (预估复杂度：高, 预估 token：~3000 / 无历史参考)
  - ⚠️ 冲突：`test_config_validation.py` 已有 ~39 个测试全面覆盖 validate_config 的所有分支和边界
- [ ] 4. 编写 `load_config()` / `_runtime_state_path()` / `load_runtime_state()` / `save_runtime_state()` 测试 (预估复杂度：中, 预估 token：~2000 / 无历史参考)
  - ⚠️ 冲突：`test_config_validation.py` 含 load_config 集成测试；`test_spec_...__config_load_robustness.py` 含 5 个异常路径测试

## 边界

### IN scope
- 新建 `tests/test_config.py`（按 proposal 原始要求）
- 覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 三个核心函数
- 使用 mock 隔离文件 I/O 和外部依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件（`test_config_validation.py` 等）
- 不修复自演进引擎的 basename 匹配 bug（这是根因，但超出本 proposal scope）

### 依赖的外部条件
- ⚠️ 需要确认：创建 `tests/test_config.py` 不会与 `test_config_validation.py`（39 个测试）产生重复维护负担
- pytest 可正常运行
- `zsiga/config.py` 模块可正常 import

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
2. `python -m pytest tests/test_config.py` 退出码 0
3. ⚠️ 新测试与已有 63+ 个测试不产生语义重复（当前成功标准无法保证这一点）

### 验收方式
- BAC-01: `test -f tests/test_config.py`
- BAC-02: `grep -c 'def test_' tests/test_config.py` ≥ 3 且包含指定三个函数名
- BAC-03: `python -m pytest tests/test_config.py` exit code 0
- BAC-04: ruff check `tests/test_config.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析，不修改）
- `tests/test_config_validation.py`（已有 39 个测试）
- `tests/test_config_diff.py`（已有 11 个测试）
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`（已有 8 个测试）
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`（已有 5 个测试）

### 项目部署分支
- deploy

### 已知风险
- **僵尸提案循环**：此 proposal 已被生成 52+ 次均未交付，执行后极可能再次被生成（根因未修复）
- **冗余测试维护**：新建 `test_config.py` 将为同一个 548 行模块引入第 5 个测试文件，增加维护负担
- **引擎 basename bug 未修复**：`zsiga/intake/evolution.py` 的 `os.path.basename()` 匹配逻辑会持续误判 config.py 无测试，反复生成此 proposal
- **BAC 过于宽松**：仅要求 3 个 test_ 函数，对于一个 548 行/CC=18 的模块是象征性覆盖

### 预估 token 消耗
- prompt: ~4000
- completion: ~2500
- 数据来源: 无历史参考（52+ 次均未执行到实现阶段）
