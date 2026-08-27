# clarify.md — add-tests-config

> ⚠️ **需求工程师批注**：此 proposal 是一个已确认的 **zombie proposal**。
> 自演进引擎的测试发现逻辑（`zsiga/intake/evolution.py`）使用 `os.path.basename()` 提取模块名 `config`，
> 仅查找精确匹配的 `tests/test_config.py`，无法发现已有的 `tests/test_config_validation.py` 等文件，
> 导致 **false negative**（误报缺少测试）。该 proposal 已被生成 **52+ 次**，全部 archived/skipped。
> 以下需求分析基于 proposal 原文，但标注了与现状的冲突。

---

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）创建 `tests/test_config.py`，覆盖公开函数，优先覆盖高复杂度函数 `validate_config`（CC=18）。

### 现状分析（与 proposal 前提冲突）
| 已有测试文件 | 覆盖内容 |
|---|---|
| `tests/test_config_validation.py`（426 行） | `validate_config` 全分支、`load_config` 集成、所有 dataclass（`LLMConfig`, `TargetConfig`, `SSHConfig`, `SafetyConfig`, `PipelineConfig`, `ConfigValidationError`, `ValidationResult`） |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | `_find_config()`, `_resolve_env_vars()` |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | `load_config` 鲁棒性 |
| `tests/test_config_diff.py`（3,717 行） | `config_diff.compare_configs()`（姊妹模块） |

**结论**：Proposal 的 BAC-02 要求的 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 均已在上述文件中存在对应测试。新建 `tests/test_config.py` 将产生**大面积重复**，不增加实质覆盖价值。

### 拆解后的子任务

- [ ] 1. 确认 `zsiga/config.py` 中未被任何现有测试文件覆盖的函数/类/分支（预估复杂度：中, 预估 token：~3000 / 无成功历史参考）
- [ ] 2. 仅针对确认的覆盖缺口，在 `tests/test_config.py` 中编写非重复的测试用例（预估复杂度：低, 预估 token：~2000 / 无成功历史参考）
- [ ] 3. 验证新建测试与已有测试无功能重复，`pytest` 全部通过（预估复杂度：低, 预估 token：~1000 / 无成功历史参考）

---

## 边界

### IN scope
- 创建 `tests/test_config.py`（新建文件）
- 仅覆盖**经确认的覆盖缺口**，不重复已有测试
- 优先关注 `validate_config`（CC=18）中未被 `test_config_validation.py` 覆盖的分支
- 可覆盖 `_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state()` 等可能缺口的函数

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改或删除任何已有测试文件
- 不修复自演进引擎的测试发现逻辑 bug（`zsiga/intake/evolution.py` 中的 basename 匹配问题）
- 不重复测试 `test_config_validation.py` 已覆盖的内容

### 依赖的外部条件
- `zsiga/config.py` 的公开 API 在执行期间不发生变更
- 现有 `tests/test_config_validation.py` 等文件可作为参考，确认哪些函数/分支已被覆盖
- `pytest` 框架可用，`ruff` lint 通过

---

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含**不与已有测试重复的**测试用例
2. 新测试覆盖了至少 1 个经确认的覆盖缺口（函数/分支）
3. `python -m pytest tests/test_config.py` 退出码 0
4. `ruff check tests/test_config.py` 无错误

### 验收方式
- 文件存在性检查：`tests/test_config.py`
- 重复性检查：与 `tests/test_config_validation.py` 和 `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` 中的测试名/逻辑对比，无功能重复
- `pytest tests/test_config.py` 退出码 0
- `ruff check tests/test_config.py` 无错误

---

## 约束

### 不能修改的文件
- `zsiga/config.py`
- 所有已有测试文件（`tests/test_config_validation.py` 等）

### 项目部署分支
- 需确认当前 deploy branch（proposal 未指定，默认为项目主分支）

### 已知风险
- **Zombie proposal 循环**（严重度：🔴 HIGH）：此 proposal 已被生成 52+ 次，全部 archived/skipped。本 clarify.md 试图通过"仅覆盖确认缺口"打破循环，但若覆盖分析结论为"无缺口"，则应直接 skip 而非强行创建空壳文件
- **重复测试风险**（严重度：🟡 MEDIUM）：BAC-02 要求的 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 在已有文件中均有对应实现，按 BAC 原样执行将产生重复
- **引擎根因未修复**（严重度：🟡 MEDIUM）：即使本次 proposal 成功创建 `tests/test_config.py`，引擎的 basename 匹配 bug 仍存在，下次扫描时可能再次生成同类 proposal（除非 `tests/test_config.py` 的存在恰好满足了 basename 匹配逻辑）

### 预估 token 消耗
- prompt: ~4000
- completion: ~2000
- 数据来源: 无成功历史参考（52+ 次均为 skipped）
