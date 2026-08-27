# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为 `zsiga/config.py`（548 行，7 函数，13 类）添加单元测试文件 `tests/test_config.py`，覆盖公开函数与数据类，重点覆盖高复杂度函数 `validate_config`（CC=18）。不修改源码。

### 拆解后的子任务

- [ ] 1. **Config 数据类测试** — 为 `ValidationResult`、`ConfigValidationError`、`SSHConfig`、`TargetConfig`、`LLMConfig` 及其余 8 个类编写构造、属性、方法测试 (预估复杂度：低, 预估 token：~2500 / 无历史参考)
- [ ] 2. **环境变量解析与校验逻辑测试** — 覆盖 `_resolve_env_vars`（环境变量替换边界）和 `validate_config`（CC=18，需覆盖多种配置结构合法/非法分支） (预估复杂度：高, 预估 token：~5000 / 无历史参考)
- [ ] 3. **配置加载管道测试** — 覆盖 `_find_config`（配置文件发现）和 `load_config`（167 行主加载函数，需 mock 文件 I/O、YAML 解析、subprocess） (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 4. **运行时状态管理测试** — 覆盖 `_runtime_state_path`、`load_runtime_state`、`save_runtime_state`（路径计算 + JSON 序列化/反序列化 + mock 文件操作） (预估复杂度：低, 预估 token：~2000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含覆盖 config.py 公开函数与类的单元测试
- 优先覆盖高 CC 函数 `validate_config`（CC=18）的所有分支
- 使用 mock 隔离文件 I/O、YAML 加载、subprocess 等外部依赖
- 每个测试可独立运行，不依赖运行时环境或外部配置文件

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改现有 `tests/test_config_validation.py` 或 `tests/test_config_diff.py`
- 不添加集成测试或端到端测试
- 不引入新的 dependencies

### 依赖的外部条件
- `zsiga/config.py` 当前接口稳定，函数签名和类结构不被其他 PR 同时修改
- `tests/test_config_validation.py` 已有部分覆盖需先确认，避免功能重复（若已覆盖 `validate_config`，则新测试聚焦增量路径）

## 目标

### 成功标准
1. `tests/test_config.py` 存在且包含 `test__find_config`、`test__resolve_env_vars`、`test_validate_config` 三个测试函数
2. 文件内至少包含 12 个 `def test_` 函数（覆盖 7 个函数 + 关键类构造）
3. `python -m pytest tests/test_config.py` 退出码 0，无 skip 无 xfail
4. `validate_config` 的分支覆盖达到主要合法/非法路径（至少 6 个测试用例）

### 验收方式
- `test -f tests/test_config.py` 确认文件存在
- `grep -c 'def test_' tests/test_config.py` 确认测试数量
- `python -m pytest tests/test_config.py -v` 退出码 0
- `ruff check tests/test_config.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py`（仅读取分析，不做任何修改）
- `tests/test_config_validation.py`（已有测试文件不触碰）
- `tests/test_config_diff.py`
- `pyproject.toml`、`requirements.txt`（不添加依赖）

### 项目部署分支
deploy

### 已知风险
- **重复覆盖风险**：`tests/test_config_validation.py` 可能已包含对 `validate_config` 或 `load_config` 的测试，实施前需先读取确认覆盖范围，避免重复
- **`load_config` 依赖链复杂**：167 行函数可能内部调用 `_find_config`、YAML 解析、env var 替换、校验等多个步骤，mock 层需要精心设计
- **自演进引擎循环**：此 proposal 由自动引擎生成，历史上同类"补测试" proposal 有空转记录（见 pattern warnings），需确保不生成与已有文件功能重叠的测试

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（同类任务无成功记录可查）
