# clarify.md — add-tests-config

## 需求拆解

### 原始需求
为无测试模块 `zsiga/config.py`（548 行, 7 函数, 13 类）添加单元测试覆盖。模块当前无直接测试文件 `tests/test_config.py`，是潜在风险点。需优先覆盖高复杂度函数 `validate_config`（CC=18），并使用 mock 隔离外部依赖。

### 拆解后的子任务

- [ ] 1. **`_find_config()` 测试** — 覆盖配置文件查找逻辑（默认路径、自定义路径、文件不存在场景）(预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 2. **`_resolve_env_vars(value)` 测试** — 覆盖环境变量替换逻辑（`${VAR}` 解析、嵌套变量、无匹配变量、非字符串输入）(预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 3. **`validate_config(config)` 测试（高优先级）** — 覆盖核心校验函数（CC=18），含合法配置、缺失必填字段、类型错误、边界条件等路径分支 (预估复杂度：高, 预估 token：~5000 / 无历史参考)
- [ ] 4. **`load_config(path)` 测试** — 覆盖完整配置加载链（YAML 解析、环境变量替换、校验集成、路径解析），需 mock 文件 I/O (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 5. **运行时状态函数测试** — 覆盖 `_runtime_state_path()`、`load_runtime_state()`、`save_runtime_state(state)` 三个函数（文件读写、默认值、路径计算）(预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 6. **数据类构造与验证测试** — 覆盖 `ValidationResult`、`ConfigValidationError`、`SSHConfig`、`TargetConfig`、`LLMConfig` 等 dataclass 的构造与属性访问 (预估复杂度：低, 预估 token：~2500 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_config.py`，包含 `zsiga/config.py` 中 7 个函数和核心类的单元测试
- 优先覆盖 `validate_config`（CC=18）的所有分支路径
- 使用 `unittest.mock` 隔离文件 I/O、环境变量、subprocess 等外部依赖
- 确保每个测试可独立运行，不依赖运行时环境

### OUT of scope
- 不修改 `zsiga/config.py` 源码
- 不修改现有测试文件 `tests/test_config_validation.py`、`tests/test_config_diff.py`
- 不测试通过其他测试文件已覆盖的集成路径
- 不涉及 dashboard、pipeline、agent 等其他模块

### 依赖的外部条件
- `zsiga/config.py` 的公开 API 在实施期间保持稳定（函数签名、类结构不变）
- pytest 和 `unittest.mock` 可用（项目已有 pytest 依赖）
- 现有 `tests/test_config_validation.py` 和 `tests/test_config_diff.py` 中的测试继续通过

## 目标

### 成功标准
1. `tests/test_config.py` 文件存在且包含至少 6 个 `def test_` 函数（覆盖 BAC-01/02/03）
2. 测试覆盖 `validate_config` 的主要分支路径（合法配置、缺失字段、类型错误）
3. `python -m pytest tests/test_config.py` 退出码 0（BAC-04）
4. 所有测试使用 mock 隔离外部依赖，不依赖真实文件系统或环境变量
5. 不修改 `zsiga/config.py` 源码

### 验收方式
- 检查 `tests/test_config.py` 文件存在
- `grep -c 'def test_' tests/test_config.py` ≥ 6
- `python -m pytest tests/test_config.py -x --tb=short` 退出码 0
- `ruff check tests/test_config.py` 无错误
- `git diff --name-only` 不包含 `zsiga/config.py`

## 约束

### 不能修改的文件
- `zsiga/config.py` — 仅读取分析，不修改源码
- `tests/test_config_validation.py` — 已有测试，不触碰
- `tests/test_config_diff.py` — 已有测试，不触碰
- `tests/conftest_zsiga.py` — 共享 fixture，不修改

### 项目部署分支
- deploy

### 已知风险
- **已有部分覆盖**：`tests/test_config_validation.py` 和 `tests/test_config_diff.py` 可能已覆盖 config.py 的部分功能，新建测试需避免重复或冲突
- **`validate_config` 高复杂度**：CC=18 意味着 18+ 条独立路径，完全覆盖需大量测试用例，可能超出单次 token 预算
- **auto-generated proposal**：此 proposal 由自演进引擎生成，历史上同类 proposal 有空转风险（26+ 次被 skip/reject 的先例），需确保不创建与已有测试重复的文件
- **配置结构耦合**：`load_config` 内部依赖多个类定义和嵌套结构，mock 编写可能较复杂

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考（同类任务无成功记录可供参考）
