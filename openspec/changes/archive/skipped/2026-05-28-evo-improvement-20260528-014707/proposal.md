# add-tests-config

## Summary
为无测试模块 `zsiga/config.py` (519 行, 4 函数, 13 类) 添加单元测试覆盖。

## Problem
模块 `zsiga/config.py` 缺少测试文件 `tests/test_config.py`，是潜在风险点。

### 当前状态（静态分析数据）
- 总行数: 519
- 函数数: 4，类数: 13
- ruff lint 问题: 0
- 圈复杂度: 平均 3.5，高 CC(>10) 函数 1 个

### 函数列表
- `_find_config()` L9-L17 (~9L)
- `_resolve_env_vars(value)` L20-L28 (~9L)
- `validate_config(config)` L296-L349 (~54L)
- `load_config(path)` L352-L518 (~167L)

### 类结构
- `ValidationResult` L32-L38 methods=['valid']
- `ConfigValidationError` L41-L44 methods=['__init__']
- `SSHConfig` L47-L53 methods=['__init__']
- `TargetConfig` L56-L80 methods=['__init__']
- `LLMConfig` L83-L93 methods=['__init__']

### Lint 问题
- 无 lint 问题

### 高复杂度函数 (CC > 10)
- `validate_config` L296 CC=18 (54L)

## Technical Design
1. 为 `zsiga/config.py` 中的公开函数编写单元测试
2. 优先覆盖高复杂度函数: `validate_config`
3. 使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess）
4. 确保每个测试可独立运行，不依赖运行时环境

### Target Files
- `tests/test_config.py` (新建)
- `zsiga/config.py` (仅读取分析，不修改)

## Acceptance Criteria
- [BAC-01] 文件 `tests/test_config.py` 存在
- [BAC-02] `tests/test_config.py` 中存在 `test__find_config`, `test__resolve_env_vars`, `test_validate_config`
- [BAC-03] `tests/test_config.py` 中存在至少 3 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_config.py` 退出码 0

## Scope
- In scope: 为 `zsiga/config.py` 编写测试，覆盖公开函数
- Out of scope: 不修改 `zsiga/config.py` 源码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（含静态分析数据）
- project=zsiga
