# clarify.md — add-tests-config

> ⚠️ **Zombie Loop Warning**: 此 proposal 已被自演进引擎生成 **52+ 次**，全部被 archived/skipped，0 次成功交付。
> 根因是引擎 `zsiga/intake/evolution.py` 的 `basename()` 匹配逻辑无法发现变体命名测试文件（如 `test_config_validation.py`），
> 误判模块"缺少测试"。以下需求拆解忠实还原 proposal 内容，但执行前务必评估是否真正需要新建文件。

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）新建 `tests/test_config.py`，添加单元测试覆盖。Proposal 声称该模块缺少测试文件。

### 已有覆盖（proposal 未识别）

| 已有测试文件 | 测试数 | 覆盖内容 |
|---|---|---|
| `tests/test_config_validation.py` | 39 | `validate_config` (CC=18 全分支)、所有 dataclass、`load_config` 集成 |
| `tests/test_config_diff.py` | — | config diff 相关 |
| `tests/test_active_target_filter.py` | 30+ | 间接覆盖 `load_runtime_state`/`save_runtime_state` |
| `tests/test_spec_..._config_unit_coverage.py` | 8 | `_find_config()`、`_resolve_env_vars()` |
| `tests/test_spec_..._config_load_robustness.py` | 5 | `load_config` 健壮性 |

**结论：7 个目标函数中至少 5 个已有直接测试覆盖，`validate_config`（最高 CC=18）已有全分支覆盖。**

### 拆解后的子任务

- [ ] 1. 分析已有测试与 proposal 目标函数的覆盖缺口，确定 `tests/test_config.py` 的增量价值（预估复杂度：低, 预估 token：~2000）
- [ ] 2. 为缺少直接覆盖的函数补充测试（若存在真正缺口）：`_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state()` 三个低 CC 函数的独立单元测试（预估复杂度：低, 预估 token：~3000）
- [ ] 3. 满足 BAC 验收：确保文件包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个指定函数名 + 至少 3 个 `def test_` + pytest 退出码 0（预估复杂度：低, 预估 token：~1000）

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含 proposal 指定的 3 个测试函数
- 覆盖 `zsiga/config.py` 中 7 个公开/私有函数
- 使用 mock 隔离文件 I/O 和环境依赖

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改 `zsiga/intake/evolution.py` 的测试发现逻辑（真正根因，但超出本 proposal 范围）
- 不删除或重构已有测试文件（`test_config_validation.py` 等）
- 不修改任何现有测试

### 依赖的外部条件
- `zsiga/config.py` 保持当前 API 不变（7 函数 + 13 类）
- pytest 测试框架可用
- `pyyaml` 可用（`load_config` 依赖）

## 目标

### 成功标准
1. 文件 `tests/test_config.py` 存在于项目 `tests/` 目录
2. 包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个函数
3. 至少 3 个 `def test_` 函数
4. `python -m pytest tests/test_config.py` 退出码 0，无失败
5. **不引入与已有测试的冗余**：新增测试应验证已有文件未覆盖的边界场景，而非简单重复

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` ≥ 3
- `grep -q 'test__find_config\|test__resolve_env_vars\|test_validate_config' tests/test_config.py`
- `python -m pytest tests/test_config.py -x --tb=short` 退出码 0
- `python -m ruff check tests/test_config.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- 所有已有测试文件（`tests/test_config_validation.py`、`tests/test_config_diff.py` 等）

### 项目部署分支
- `deploy`（项目自身目标）

### 已知风险
- **Zombie loop 风险（严重）**：此 proposal 已生成 52+ 次未成功，属于引擎 basename 匹配 bug 的症状。即使本次成功创建 `tests/test_config.py`，引擎仍可能因发现逻辑缺陷继续生成同名 proposal
- **冗余风险**：`validate_config`（CC=18）已有 39 个测试覆盖全分支，新增测试大概率重复
- **验收冲突**：BAC-02 要求 `test__find_config` 和 `test__resolve_env_vars`，这两个函数已在 `test_spec_..._config_unit_coverage.py` 中覆盖（8 个测试），新测试价值存疑
- **根因未修**：真正需要修复的是 `zsiga/intake/evolution.py` L1084-1094 的测试文件发现逻辑，但不在本 proposal scope 内

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 52+ 次均未执行到实现阶段）
