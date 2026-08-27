# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行，7 函数，13 类）添加单元测试覆盖。Proposal 声称该模块"缺少测试文件"，但**实际上 `tests/test_config_validation.py`（426 行，30+ 测试函数）已存在**，覆盖了 `validate_config`（CC=18 的核心函数）、`ValidationResult`、`ConfigValidationError`、`LLMFastastConfig` 及 `load_config` 的集成测试。本需求应聚焦于**尚未被覆盖的函数**（`_find_config`、`_resolve_env_vars`、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state`），而非重复已有覆盖。

### 拆解后的子任务

- [ ] 1. **创建 `tests/test_config.py` 并覆盖内部工具函数** — 测试 `_find_config()`（配置文件定位逻辑，含默认路径与环境变量覆盖）和 `_resolve_env_vars(value)`（`${VAR}` 模式替换，含无匹配/嵌套/空值等边界）。预估复杂度：低，预估 token：~2500 / 无历史参考
- [ ] 2. **覆盖运行时状态管理函数** — 测试 `_runtime_state_path()`（路径计算）、`load_runtime_state()`（文件读取与缺省回退）、`save_runtime_state(state)`（YAML 序列化写入），需 mock 文件 I/O。预估复杂度：低，预估 token：~2000 / 无历史参考
- [ ] 3. **补充 `validate_config` 边界场景与类构造测试** — `test_config_validation.py` 已覆盖主路径，本文件补充：空 config、部分字段缺失、SSHConfig/TargetConfig/LLMConfig 的构造与默认值验证。预估复杂度：中，预估 token：~3000 / 无历史参考
- [ ] 4. **确认无重复覆盖并确保全量测试通过** — 验证新文件与 `test_config_validation.py` 无矛盾，`pytest tests/test_config.py` 退出码 0，且 `pytest tests/test_config_validation.py` 仍通过。预估复杂度：低，预估 token：~500 / 无历史参考

## 边界

### IN scope
- 新建 `tests/test_config.py`，测试 `_find_config`、`_resolve_env_vars`、`_runtime_state_path`、`load_runtime_state`、`save_runtime_state` 等 `test_config_validation.py` 未覆盖的函数
- 补充 `validate_config` 的边界场景（空/残缺 config）
- 补充 `SSHConfig`、`TargetConfig`、`LLMConfig` 等数据类的构造测试
- 使用 mock 隔离文件 I/O 和环境变量

### OUT of scope
- 修改 `zsiga/config.py` 源码（仅读取分析）
- 修改或移动已有的 `tests/test_config_validation.py`
- 重复 `test_config_validation.py` 已覆盖的 `validate_config` 主路径测试
- 修改 `zsiga.yaml` 或其他配置文件

### 依赖的外部条件
- `zsiga/config.py` 保持当前 API 签名不变
- `tests/test_config_validation.py` 已有覆盖不与新测试产生 import 冲突
- pytest 可正常发现并执行 `tests/test_config.py`

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含 ≥ 3 个 `def test_` 函数
2. 至少覆盖 `_find_config`、`_resolve_env_vars`、`validate_config`（边界）三个函数的测试
3. `python -m pytest tests/test_config.py` 退出码 0
4. `python -m pytest tests/test_config_validation.py` 退出码 0（已有测试不被破坏）
5. 新测试与已有 `test_config_validation.py` 无函数名冲突

### 验收方式
- 检查 `tests/test_config.py` 文件存在性
- `grep -c "def test_" tests/test_config.py` ≥ 3
- `python -m pytest tests/test_config.py -q` 通过
- `python -m pytest tests/test_config_validation.py -q` 通过（回归守卫）
- `grep "test_validate_config" tests/test_config.py` 不与 `test_config_validation.py` 中的同名函数产生冲突（用不同的函数名或确保覆盖不同场景）

## 约束

### 不能修改的文件
- `zsiga/config.py` — 源码只读
- `tests/test_config_validation.py` — 已有测试不动
- `pyproject.toml`、`requirements.txt` — 不新增依赖

### 项目部署分支
待确认（通常为 `main` 或 `deploy`）

### 已知风险
- **重复覆盖风险**：`test_config_validation.py` 已有 426 行覆盖 `validate_config`，新文件需避免测试同一路径；建议新文件中 `validate_config` 测试聚焦边界/异常场景，并使用不冲突的函数名（如 `test_validate_config_empty_input`、`test_validate_config_partial_fields`）
- **auto-generated proposal 质量**：此 proposal 由自演进引擎生成，静态分析声称"模块缺少测试文件"与事实不符（已有 426 行测试）；执行时需以本 clarify.md 的分析为准
- **私有函数测试**：`_find_config`、`_resolve_env_vars` 等以下划线开头的函数属模块内部实现，测试可能随源码重构而脆弱

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（同类任务 `verify-layer0-with-tests` 在 verify 阶段有失败记录，但模式不完全相同）
