# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行, 7 函数, 13 类）创建 `tests/test_config.py`，编写单元测试覆盖公开函数，优先覆盖高复杂度函数 `validate_config`(CC=18)。

### 现有覆盖事实（必须纳入考量）
- `tests/test_config_validation.py`（426 行, 40+ 测试）已覆盖：`validate_config`、`load_config` 集成测试、`ValidationResult`、`ConfigValidationError`、`LLMFastConfig`、`SSHConfig`、`TargetConfig` 等数据类构造。
- `tests/test_config_diff.py`（98 行）已覆盖 config diff。
- `tests/test_spec_evo_improvement_..._config_unit_coverage.py` 已覆盖：`_find_config`、`_resolve_env_vars`、`_runtime_state_path`。
- **真正缺失的直接单元测试**：`load_runtime_state()` 和 `save_runtime_state()`。

### 拆解后的子任务

- [ ] 1. **运行时状态持久化测试模块** — 创建 `tests/test_config.py`，编写 `load_runtime_state()` 和 `save_runtime_state()` 的直接单元测试，覆盖正常读写、文件不存在、YAML 解析失败等场景。使用 `tmp_path` 隔离文件 I/O，mock `_runtime_state_path()` 指向临时目录。（预估复杂度：低, 预估 token：~3000 / 无同类成功历史参考）
- [ ] 2. **补充已有测试未覆盖的边界场景** — 在 `tests/test_config.py` 中补充 `load_config()` 的边缘 case（空 YAML、缺少必要字段、类型错误），以及 `CompactionConfig`/`SafetyConfig`/`IntakeConfig`/`PipelineConfig`/`GithubConfig`/`LoggingConfig`/`ZsigaConfig` 等数据类的默认值和构造测试（如果 `test_config_validation.py` 未完全覆盖的话）。（预估复杂度：中, 预估 token：~5000 / 无同类成功历史参考）
- [ ] 3. **lint 与集成验证** — 运行 `ruff check tests/test_config.py` 和 `python -m pytest tests/test_config.py`，确保无 lint 错误且全部测试通过。（预估复杂度：低, 预估 token：~1000 / 无历史参考）

## 边界

### IN scope
- 创建 `tests/test_config.py`（新文件）
- 为 `load_runtime_state()` 和 `save_runtime_state()` 编写直接单元测试
- 补充 `load_config()` 和各数据类的边缘场景测试（与已有测试不重复）
- 满足 BAC-01 ~ BAC-04

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改 `tests/test_config_validation.py` 或其他已有测试文件
- 不重复覆盖已有测试已充分测试的函数（如 `validate_config` 的核心逻辑已在 `test_config_validation.py` 中有 30+ 测试）
- 不创建与 `test_config_validation.py` 功能重叠的测试

### 依赖的外部条件
- `zsiga/config.py` 中 `load_runtime_state()` / `save_runtime_state()` 的实现签名不变
- `tests/test_config_validation.py` 及其他已有测试文件保持现有覆盖，不会被删除或大幅重构
- pytest 和 ruff 工具链可用

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 文件中存在 `test__find_config`、`test__resolve_env_vars`、`test_validate_config`（满足 BAC-02），**但不得与 `test_config_validation.py` 中的测试逻辑重复**——这些函数名应聚焦于已有测试未覆盖的边界场景
3. `load_runtime_state()` 和 `save_runtime_state()` 获得直接单元测试覆盖（这是真正的新增价值）
4. `python -m pytest tests/test_config.py` 退出码 0
5. `ruff check tests/test_config.py` 无错误

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c "def test_" tests/test_config.py` 确认 ≥3
- `grep -E "test__find_config|test__resolve_env_vars|test_validate_config" tests/test_config.py` 确认 BAC-02 函数名存在
- `python -m pytest tests/test_config.py -v` 确认全部通过（exit 0）
- 人工审查：新增测试与 `test_config_validation.py` 不存在实质性重复

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析）
- `tests/test_config_validation.py`（已有 426 行测试，不可触碰）
- `tests/test_config_diff.py`
- `tests/test_spec_evo_improvement_*_config_*.py`

### 项目部署分支
- 需从 git 环境确认（proposal 未指定，默认 `main`）

### 已知风险
- **重复测试风险**：BAC-02 要求 `test_validate_config`，但 `test_config_validation.py` 已有 30+ 个 `validate_config` 测试。新测试必须聚焦**不同场景**（如极端边界 case），否则是纯冗余。
- **同名 proposal 循环**：历史记录显示 `add-tests-config` 类 proposal 已迭代 22+ 次均未交付，存在 zombie proposal 模式风险。本次执行需严格聚焦"真正缺失的覆盖"而非机械满足 BAC。
- **数据类构造测试可能已存在**：`test_config_validation.py` 已包含 `TestSSHConfigConstruction`、`TestTargetConfigDefaults`、`TestLLMConfigDefaults` 等 13 个测试类，新增数据类测试前必须确认不重复。

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 无成功交付记录）
