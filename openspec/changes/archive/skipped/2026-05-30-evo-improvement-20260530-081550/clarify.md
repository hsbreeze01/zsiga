# clarify.md — add-tests-config

## 需求拆解

### 原始需求
Proposal 声称 `zsiga/config.py` (548行, 7函数, 13类) 缺少测试文件 `tests/test_config.py`，要求添加单元测试覆盖，重点覆盖高复杂度函数 `validate_config` (CC=18)。

### ⚠️ 前提验证失败
**`zsiga/config.py` 已有完善的测试覆盖，无需新建 `tests/test_config.py`。**

经验证，以下测试文件已覆盖 config.py 的全部公开符号：

| 测试文件 | 行数 | test函数数 | 覆盖范围 |
|----------|------|-----------|----------|
| `tests/test_config_validation.py` | 426行 | 39个 | `ValidationResult`, `validate_config`, `ConfigValidationError`, `load_config` 集成, `LLMFastConfig`, 数据类构造 |
| `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` | ~100行 | 8个 | `_find_config`, `_resolve_env_vars` |
| `tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py` | ~80行 | 5个 | `load_config` 健壮性 |

**已覆盖的 config.py 符号清单：**
- ✅ `_find_config()` — 在 config_unit_coverage spec 测试中覆盖
- ✅ `_resolve_env_vars(value)` — 在 config_unit_coverage spec 测试中覆盖
- ✅ `validate_config(config)` CC=18 — 在 test_config_validation.py 中有 20+ 个测试（TestValidConfig, TestMissingLLMFields, TestTemperatureWarning, TestMaxTokensWarning, TestTargetValidation, TestPipelineWarnings）
- ✅ `load_config(path)` — 在 test_config_validation.py (TestLoadConfigIntegration 3个) + config_load_robustness (5个) 中覆盖
- ✅ `ValidationResult` — TestValidationResult (3个)
- ✅ `ConfigValidationError` — TestConfigValidationError (2个)
- ✅ `SSHConfig` — 在 TestTargetValidation 中使用
- ✅ `TargetConfig` — 在 TestTargetValidation 中使用
- ✅ `LLMConfig` — 在 TestMissingLLMFields, TestTemperatureWarning, TestMaxTokensWarning 中使用
- ✅ `LLMFastConfig` — TestLLMFastConfig (8个)
- ✅ `PipelineConfig` — TestPipelineWarnings (5个)
- ✅ `IntakeConfig`, `SafetyConfig`, `ZsigaConfig` — 通过 _make_config helper 全面使用
- ⚠️ `_runtime_state_path()`, `load_runtime_state()`, `save_runtime_state()` — 可能未直接覆盖（需确认）

**根因：** 自演进引擎用 `test_{basename}.py` 模式（即 `test_config.py`）查找测试文件，但项目实际命名为 `test_config_validation.py`，导致引擎误判为"缺少测试"。这与 runner.py (`test_harness_runner.py`) 和 transport.py 的空转循环属同一类 bug。

### 拆解后的子任务
> 以下任务仅当确认存在真实测试缺口时才应执行。

- [ ] 1. 补充 `_runtime_state_path` / `load_runtime_state` / `save_runtime_state` 测试（预估复杂度：低, 预估 token：~2000）
  - 文件范围：`tests/test_config_validation.py`（追加）或新建小文件
  - 仅当这三个函数未被任何测试覆盖时才需要
- [ ] 2. 无其他必要任务 — config.py 的核心功能（validate_config, load_config, _find_config, _resolve_env_vars, 所有数据类）已有完整覆盖

## 边界

### IN scope
- 验证 `_runtime_state_path`, `load_runtime_state`, `save_runtime_state` 是否已有间接覆盖
- 如确认未覆盖，补充这三个函数的单元测试

### OUT of scope
- ❌ 创建 `tests/test_config.py` — 冗余，已有 `test_config_validation.py` 覆盖
- ❌ 重新覆盖 `validate_config` — 已有 20+ 个测试
- ❌ 重新覆盖 `load_config` — 已有 8+ 个测试
- ❌ 重新覆盖数据类构造 — 已全面覆盖
- ❌ 修改 `zsiga/config.py` 源码

### 依赖的外部条件
- pytest 运行环境正常
- `zsiga.config` 模块可正常 import

## 目标

### 成功标准
1. 确认 config.py 的测试缺口（如有）仅限于 `_runtime_state_path` / `load_runtime_state` / `save_runtime_state`
2. 如有缺口，补充测试后 `python -m pytest tests/ -x` 退出码 0
3. 不创建与已有测试功能重叠的冗余文件

### 验收方式
- `grep -rn 'runtime_state\|load_runtime_state\|save_runtime_state' tests/` 确认覆盖状态
- `python -m pytest tests/test_config_validation.py -v` 全部通过
- `python -m pytest tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py -v` 全部通过

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取，不修改）
- 已有的测试文件不应被破坏性修改（可追加测试）

### 项目部署分支
- zsiga-l5-autonomous-engineer

### 已知风险
- **虚假前提风险（高）**：Proposal 基于错误的"config.py 缺少测试"前提。实际已有 52+ 个测试覆盖 config.py 的 13 个类和核心函数。执行 proposal 的 BAC（创建 `tests/test_config.py`）会产出冗余文件。
- **引擎扫描 bug**：自演进引擎用 basename 匹配 `test_config.py`，无法发现 `test_config_validation.py`，导致持续生成虚假 proposal。
- **历史模式匹配**：此 proposal 与 runner.py (27+ 次循环被拒)、transport.py (12+ 次循环被 skip)、duration_predictor.py (pushback) 属完全相同的空转模式。

### 预估 token 消耗
- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考（同类 proposal 均被 reject/skip，无成功执行记录）
