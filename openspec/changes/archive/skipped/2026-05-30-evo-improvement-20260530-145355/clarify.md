# clarify.md — add-tests-config

> **⚠️ 僵尸提案警告**：此 proposal 已被自演进引擎循环生成 **52+ 次**，全部 archived/skipped，无一成功交付。
> 根因是引擎的 basename 匹配逻辑（`evolution.py` L614/L1093-1098）只查找精确命名的 `test_config.py`，
> 无法发现实际存在的 `test_config_validation.py`、`test_config_diff.py` 等文件。
> **执行此 proposal 只会创建一个与已有测试高度重叠的冗余文件，无法阻止引擎继续生成同名提案。**

---

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）创建 `tests/test_config.py`，声称该模块缺少测试文件。

**事实核查**：以下测试文件已存在并覆盖了该模块的大部分公开 API：

| 已有测试文件 | 测试数 | 覆盖范围 |
|---|---|---|
| `tests/test_config_validation.py` | ~39 | `validate_config`、`load_config`、全部 13 个 dataclass |
| `tests/test_config_diff.py` | ~12 | `compare_configs` |
| `tests/test_active_target_filter.py` | ~30+ | 间接覆盖 `load_runtime_state` / `save_runtime_state` |

7 个目标函数中至少 5 个已有直接测试覆盖（`validate_config`、`load_config`、`_find_config`、`_resolve_env_vars`、`load_runtime_state`/`save_runtime_state`）。

### 拆解后的子任务

- [ ] 1. **评估增量覆盖缺口** — 分析已有 `test_config_validation.py`（~39 tests）和 `test_config_diff.py`（~12 tests）的实际覆盖，确定 `tests/test_config.py` 能提供哪些不重复的测试价值 (预估复杂度：中, 预估 token：~4000 / 无有效历史参考)
- [ ] 2. **创建 `tests/test_config.py`** — 按 BAC 要求创建文件，包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数，确保与已有测试不重复 (预估复杂度：低, 预估 token：~3000 / 无有效历史参考)
- [ ] 3. **运行 pytest 验证** — 确认 `python -m pytest tests/test_config.py` 退出码 0 (预估复杂度：低, 预估 token：~1000 / 无有效历史参考)

---

## 边界

### IN scope
- 创建 `tests/test_config.py`（新文件）
- 为 `zsiga/config.py` 的公开函数编写测试（至少 3 个 `def test_` 函数）
- 满足 4 条 BAC 验收标准

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改已有测试文件（`test_config_validation.py`、`test_config_diff.py`）
- 不修复 `zsiga/intake/evolution.py` 的 basename 匹配 bug（这才是循环根因）

### 依赖的外部条件
- `zsiga/config.py` 模块结构不变（13 类 + 7 函数）
- pytest 环境可用
- 已有测试文件（`test_config_validation.py` 等）不被删除或移动

---

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
2. `python -m pytest tests/test_config.py` 退出码 0
3. 新测试与已有测试（`test_config_validation.py` ~39 tests）不产生功能重复

### 验收方式
- 文件存在性检查：`test -f tests/test_config.py`
- 符号存在性检查：`grep -c 'def test_' tests/test_config.py` ≥ 3
- pytest 执行：`python -m pytest tests/test_config.py` 退出码 0
- **注意**：即使所有 BAC 通过，此 proposal 的核心价值仍然存疑——已有测试已覆盖目标模块

---

## 约束

### 不能修改的文件
- `zsiga/config.py`（proposal scope 明确排除）
- `zsiga/intake/evolution.py`（不在 scope 内，但包含导致此 proposal 循环生成的 basename 匹配 bug）

### 项目部署分支
- （未在 proposal 中指定，需确认）

### 已知风险
1. **僵尸循环风险（HIGH）**：此 proposal 已被生成 52+ 次，全部失败。即使本次成功创建 `test_config.py`，引擎的 basename 匹配逻辑不会被修复，未来可能继续生成同类 proposal
2. **测试重复风险（MEDIUM）**：`test_config_validation.py` 已有 ~39 个测试覆盖 `validate_config`、`load_config` 等，新文件极易产出功能重复的测试
3. **虚假前提风险（HIGH）**：proposal 声称"模块缺少测试文件"，但已有至少 2 个专用测试文件 + 1 个间接覆盖文件。问题陈述建立在错误事实之上
4. **根因未修复（HIGH）**：`evolution.py` 的 basename 匹配 bug（L614: `os.path.basename()`）才是真正需要修复的问题，但不在本 proposal scope 内

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 全部 skipped，无成功执行记录可供参考）
