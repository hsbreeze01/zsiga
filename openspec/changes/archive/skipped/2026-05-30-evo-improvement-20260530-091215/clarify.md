# clarify.md — add-tests-config

> **⚠️ 需求工程师判定：此 proposal 基于虚假前提，属于 zombie proposal（已迭代 22+ 次均被 skip/reject）。核心前提"模块缺少测试"不成立。**

## 需求拆解

### 原始需求
Proposal 声称 `zsiga/config.py`（548 行, 7 函数, 13 类）缺少测试文件 `tests/test_config.py`，要求为其公开函数编写单元测试。

### 事实核查结果
**前提不成立**。`zsiga/config.py` 已有 52+ 个测试函数分布在多个测试文件中：

| 已有测试文件 | 测试数 | 覆盖范围 |
|---|---|---|
| `tests/test_config_validation.py` (426 行) | ~39 | `validate_config`(CC=18 全分支)、所有 data class 构造、`load_config` 集成、`LLMFastConfig`、`ConfigValidationError` |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | 8 | `_find_config()`、`_resolve_env_vars()` |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | 5 | `load_config` 健壮性 |
| + 10 个间接测试文件 | — | `TargetConfig`、`GithubConfig` 等 |

**BAC 条件实质已满足**：
- BAC-01（文件存在）：`tests/test_config.py` 不存在，但等价覆盖在其他文件中
- BAC-02（测试函数）：`test__find_config`、`test__resolve_env_vars`、`test_validate_config` 已在上述文件中覆盖
- BAC-03（≥3 个 test_）：52+ 个
- BAC-04（pytest 通过）：已有测试均可运行

### 根因分析
自演进引擎 `zsiga/intake/evolution.py` 使用 `os.path.basename()` 提取模块名 `config`，然后仅查找 `tests/test_config.py`，无法发现实际命名的 `test_config_validation.py`、`test_spec_evo_improvement_..._config_unit_coverage.py` 等文件，导致反复生成此 proposal。

### 拆解后的子任务

**方案 A（推荐）：标记 No-Op，不执行**
- [ ] 1. 将此 change 标记为 no-op（创建 no-op 说明文件），明确记录已有测试覆盖情况 (预估复杂度：低, 预估 token：~500)

**方案 B（如强制执行）：创建冗余测试文件**
- [ ] 1. 创建 `tests/test_config.py`，包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 等测试函数，与已有测试不冲突 (预估复杂度：低, 预估 token：~2000)
- [ ] 2. 运行 pytest 验证新文件通过且不破坏现有测试 (预估复杂度：低, 预估 token：~500)

## 边界

### IN scope
- 为 `zsiga/config.py` 添加测试（仅当方案 B 被选择时）
- 测试覆盖公开函数：`_find_config`、`_resolve_env_vars`、`validate_config`

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件
- 不修复自演进引擎的测试发现逻辑（那是另一个独立问题）

### 依赖的外部条件
- `zsiga/config.py` 的公开 API 在执行期间不发生变化
- 已有测试文件 (`test_config_validation.py` 等) 保持不变
- pytest 环境可用

## 目标

### 成功标准
1. **方案 A**：change 目录包含 no-op 说明文件，记录已有覆盖情况及引擎缺陷根因
2. **方案 B**：`tests/test_config.py` 存在，包含 ≥3 个 `def test_` 函数，`pytest tests/test_config.py` 退出码 0

### 验收方式
- 方案 A：检查 no-op 文件存在且内容准确引用已有测试文件
- 方案 B：BAC-01~BAC-04 全部通过（文件存在、函数存在、≥3 个测试、pytest 退出码 0）

## 约束

### 不能修改的文件
- `zsiga/config.py`（proposal 明确声明仅读取分析）
- `tests/test_config_validation.py`（已有 39 个测试，不碰）
- `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`
- `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`

### 项目部署分支
- deploy branch：待确认（proposal 标注 `project=zsiga`）

### 已知风险
- **虚假前提风险（高）**：已有 52+ 个测试覆盖该模块，创建新测试文件属于冗余劳动
- **zombie proposal 循环（高）**：此 proposal 已迭代 22+ 次均被 skip/reject，执行后不会阻止引擎继续生成同名 proposal
- **引擎根因未修复（高）**：`zsiga/intake/evolution.py` 的测试发现逻辑缺陷未修复，将持续产生类似 proposal（`add-tests-runner`、`add-tests-config` 等）
- **重复测试维护负担（低）**：若创建 `tests/test_config.py`，同一逻辑将有两套测试需要维护

### 预估 token 消耗
- 方案 A：prompt ~800, completion ~300
- 方案 B：prompt ~2000, completion ~1500
- 数据来源: 无历史参考（同类 proposal 从未成功交付）
