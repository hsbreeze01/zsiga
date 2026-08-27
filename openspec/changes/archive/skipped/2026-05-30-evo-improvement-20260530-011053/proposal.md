# add-tests-transport

## Summary
为无测试模块 `zsiga/transport.py` (96 行, 1 函数, 3 类) 添加单元测试覆盖。

## Problem
模块 `zsiga/transport.py` 缺少测试文件 `tests/test_transport.py`，是潜在风险点。

### 当前状态（静态分析数据）
- 总行数: 96
- 函数数: 1，类数: 3
- ruff lint 问题: 0
- 圈复杂度: 平均 2.0，高 CC(>10) 函数 0 个

### 函数列表
- `create_transport(target_config)` L86-L95 (~10L)

### 类结构
- `Transport` L6-L13 methods=['run_shell', 'close']
- `LocalTransport` L16-L24 methods=['run_shell']
- `SSHTransport` L27-L83 methods=['__init__', '_ensure_control', '_base_args', '_target', 'run_shell', 'close']

### Lint 问题
- 无 lint 问题

### 高复杂度函数 (CC > 10)
- 无高复杂度函数 (CC>10)

## Technical Design
1. 为 `zsiga/transport.py` 中的公开函数编写单元测试
2. 优先覆盖高复杂度函数: (无高 CC 函数)
3. 使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess）
4. 确保每个测试可独立运行，不依赖运行时环境

### Target Files
- `tests/test_transport.py` (新建)
- `zsiga/transport.py` (仅读取分析，不修改)

## Acceptance Criteria
- [BAC-01] 文件 `tests/test_transport.py` 存在
- [BAC-02] `tests/test_transport.py` 中存在 `test_create_transport`
- [BAC-03] `tests/test_transport.py` 中存在至少 1 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_transport.py` 退出码 0

## Scope
- In scope: 为 `zsiga/transport.py` 编写测试，覆盖公开函数
- Out of scope: 不修改 `zsiga/transport.py` 源码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（含静态分析数据）
- project=zsiga
