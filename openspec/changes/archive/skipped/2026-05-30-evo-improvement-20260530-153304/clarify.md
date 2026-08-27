# clarify.md — add-tests-config

> **⚠️ 前提校验警告**：并行探索确认 `zsiga/config.py` **已有充分测试覆盖**（52+ 直接测试函数，跨 3 个专用测试文件 + 7 个间接文件）。此 proposal 的核心前提"缺少测试文件"是**不准确的**。根因是 `zsiga/intake/evolution.py` 的 `basename()` 匹配逻辑只能发现 `test_config.py`，无法发现 `test_config_validation.py` 等变体命名。此 proposal 已循环生成 **52+ 次**，全部 archived/skipped，是典型的 zombie proposal。

---

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548行，7函数，13类）创建 `tests/test_config.py`，声称该模块缺少测试覆盖。目标包括 `_find_config`、`_resolve_env_vars`、`validate_config` 等函数的单元测试。

### 已有覆盖（探索确认）
| 现有测试文件 | 测试数 | 覆盖范围 |
|---|---|---|
| `tests/test_config_validation.py` | 39 | `validate_config` 全分支（CC=18）、所有 data class、`load_config` 集成 |
| `tests/test_config_diff.py` | — | config diff 对比 |
| `test_spec_evo_*_config_unit_coverage.py` | 8 | `_find_config()`, `_resolve_env_vars()` |
| `test_spec_evo_*_config_load_robustness.py` | 5 | `load_config` 健壮性 |
| + 7 个间接测试文件 | — | `TargetConfig`, `GithubConfig` 等 |

**结论：`validate_config`、`_find_config`、`_resolve_env_vars`、`load_config` 已有直接覆盖；`_runtime_state_path`、`load_runtime_state`、`save_runtime_state` 可能有间接覆盖但缺乏专用测试。**

### 拆解后的子任务
- [ ] 1. 创建 `tests/test_config.py`，仅包含**已有测试未覆盖的增量部分**（`_runtime_state_path`、`load_runtime_state`、`save_runtime_state` 三个运行时状态函数），避免与 `test_config_validation.py` 的 39 个测试重复（预估复杂度：低，预估 token：~2000 / 无历史参考）
- [ ] 2. 验证新测试文件通过 `python -m pytest tests/test_config.py` 且不与现有测试冲突（预估复杂度：低，预估 token：~500 / 无历史参考）

---

## 边界

### IN scope
- 创建 `tests/test_config.py` 文件，覆盖 `_runtime_state_path`、`load_runtime_state`、`save_runtime_state` 三个运行时状态函数（已有覆盖盲区）
- 使用 mock 隔离文件 I/O 依赖
- 确保与现有 `tests/test_config_validation.py` 不重复

### OUT of scope
- **不修改** `zsiga/config.py` 源码
- **不重复覆盖** `validate_config`（已在 `test_config_validation.py` 中有 CC=18 全分支覆盖）
- **不重复覆盖** `_find_config`、`_resolve_env_vars`（已在 `test_spec_evo_*` 文件中覆盖）
- **不修复** `zsiga/intake/evolution.py` 的 basename 匹配 bug（根因问题，需单独 proposal）

### 依赖的外部条件
- `zsiga/config.py` 源码结构不变（7 函数 13 类）
- 现有 `tests/test_config_validation.py` 等 52+ 测试持续通过
- pytest 可正常运行

---

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含至少 3 个 `test_` 函数
2. 文件中包含 `test__runtime_state_path`、`test_load_runtime_state`、`test_save_runtime_state`（或等价命名）
3. `python -m pytest tests/test_config.py` 退出码 0
4. `python -m pytest tests/` 全量测试仍通过（无回归）
5. 新测试与已有 `test_config_validation.py` 无功能重复

### 验收方式
- `test -f tests/test_config.py`
- `grep -c "def test_" tests/test_config.py` ≥ 3
- `python -m pytest tests/test_config.py -v` 退出码 0
- `python -m pytest tests/ --tb=short` 无额外失败

---

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/test_config_validation.py`（现有 39 测试不可变动）
- `zsiga/intake/evolution.py`（根因 bug 不在本 scope 内）

### 项目部署分支
- deploy 分支信息未在 proposal 中指定，需确认 `zsiga.yaml` 中 target `zsiga` 的 `deploy_branch`

### 已知风险
- **zombie 循环风险（严重）**：此 proposal 已循环生成 52+ 次全部失败，执行后大概率被后续 cycle 再次生成。即使本文件落地，根因 bug 未修，引擎仍会继续生成重复 proposal
- **重复覆盖风险**：若实现者忽略已有 52+ 测试而盲目创建"全覆盖"文件，将与 `test_config_validation.py` 大量重复，增加维护负担
- **虚假前提风险**：proposal 声称"模块缺少测试文件"但实际已有充分覆盖，可能导致执行方向偏差
- **BAC-02 与已有测试冲突**：proposal 要求 `test__find_config`、`test__resolve_env_vars`、`test_validate_config`，但这三个函数已被现有测试文件覆盖，创建同名测试函数将导致语义重复

### 预估 token 消耗
- prompt: ~1500
- completion: ~1000
- 数据来源: 无历史参考（此任务从未成功执行过）
