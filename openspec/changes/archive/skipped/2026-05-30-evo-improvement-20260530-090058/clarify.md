# clarify.md — add-tests-config

## 需求拆解

### 原始需求
Proposal 声称 `zsiga/config.py`（548 行, 7 函数, 13 类）缺少测试文件 `tests/test_config.py`，要求为公开函数编写单元测试，优先覆盖高 CC 函数 `validate_config`（CC=18）。

### ⚠️ 前提验证结果：需求不成立

**proposal 的核心前提"模块缺少测试"是错误的。** 经验证，`zsiga/config.py` 已有全面的测试覆盖，分布在多个现有测试文件中：

| 测试文件 | 测试函数数 | 覆盖范围 |
|---|---|---|
| `tests/test_config_validation.py` | 39 | `validate_config`（CC=18 完整覆盖）、所有 data class（`ValidationResult`, `ConfigValidationError`, `SSHConfig`, `TargetConfig`, `LLMConfig`, `LLMFastConfig`, `PipelineConfig`, `IntakeConfig`, `SafetyConfig`, `ZsigaConfig`）、`load_config` 集成测试 |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | 8 | `_find_config()`、`_resolve_env_vars()` |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | 5 | `load_config` 鲁棒性 |
| `tests/test_active_target_filter.py` | 12 | 导入 config 符号 |
| `tests/test_target_manifest.py` | 15 | `TargetConfig`, `load_config`, `validate_config` |
| `tests/test_venv_usage.py` | 16 | `TargetConfig`, `load_config` |
| `tests/test_github_issue.py` | 19 | `GithubConfig`, `load_config` |
| `tests/test_token_budget.py` | 24 | config 相关符号 |

**总计：13 个测试文件直接导入 `zsiga.config`，其中核心 config 专属测试文件含 52 个测试函数。**

proposal 列出的 7 个函数全部已有测试覆盖：
- `_find_config()` → `test_spec_evo_improvement_..._config_unit_coverage.py`（2 个测试）
- `_resolve_env_vars()` → 同上（6 个测试）
- `validate_config()` → `test_config_validation.py`（~20 个测试，含 CC=18 全分支覆盖）
- `load_config()` → `test_config_validation.py`（集成测试）+ `config_load_robustness.py`（鲁棒性测试）
- `_runtime_state_path()` / `load_runtime_state()` / `save_runtime_state()` → 被其他集成测试间接覆盖

### 根因分析
与 `runner.py` 空转模式相同：自演进引擎的测试发现逻辑使用 `os.path.basename()` 提取模块名 `config`，然后仅查找 `tests/test_config.py`，无法发现实际命名为 `test_config_validation.py`、`test_spec_evo_improvement_..._config_unit_coverage.py` 等的测试文件。

### 拆解后的子任务

> **注意：以下子任务仅在忽略上述前提验证结果时才有意义。建议直接 REJECT 此 proposal。**

- [ ] 1. ~~创建 `tests/test_config.py` 并为 `_find_config`、`_resolve_env_vars`、`validate_config` 编写测试~~ (预估复杂度：低, 预估 token：~3000 / 无历史参考 — **与已有测试完全冗余**)

## 边界

### IN scope
- 创建 `tests/test_config.py`（新建文件）
- 覆盖 `_find_config`、`_resolve_env_vars`、`validate_config` 三个函数

### OUT of scope
- 不修改 `zsiga/config.py` 源码（proposal 原始约束）

### 依赖的外部条件
- `zsiga/config.py` 中各 data class 和函数签名不变
- `pytest` 可正常运行

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在
2. 文件中包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
3. 包含至少 3 个 `def test_` 函数
4. `python -m pytest tests/test_config.py` 退出码 0

> **警告：以上标准全部可满足，但产出物与已有 52 个测试完全冗余，无增量价值。**

### 验收方式
- `pytest tests/test_config.py` 通过
- 文件内容包含指定函数名
- 不引入 ruff lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- 所有现有测试文件

### 项目部署分支
- deploy

### 已知风险
1. **🔴 核心风险：虚假前提** — proposal 声称"缺少测试"但 `zsiga/config.py` 已有 52+ 个直接测试函数分布在 3 个专用测试文件中，另有 10 个间接测试文件。创建 `tests/test_config.py` 纯属冗余。
2. **🟡 引擎空转风险** — 与 `runner.py` 模式相同，自演进引擎因 `basename()` 匹配缺陷无法发现已有测试，将持续生成同类 proposal 形成死循环。
3. **🟡 测试冲突风险** — 新建 `tests/test_config.py` 可能与已有测试产生 fixture 冲突或命名碰撞。
4. **建议操作** — REJECT 此 proposal，修复 `zsiga/intake/evolution.py` 中的测试文件发现逻辑（将 `test_{basename}.py` 扩展为模糊匹配 `test_*{basename}*.py`）。

### 预估 token 消耗
- prompt: ~2000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 均被 reject/skip）
