# add-tests-duration_predictor

## Summary
为无测试模块 `zsiga/duration_predictor.py` (164 行, 5 函数) 添加单元测试覆盖。

## Problem
模块 `zsiga/duration_predictor.py` 缺少测试文件 `tests/test_duration_predictor.py`，是潜在风险点。

### 当前状态（静态分析数据）
- 总行数: 164
- 函数数: 5，类数: 0
- ruff lint 问题: 0
- 圈复杂度: 平均 4.8，高 CC(>10) 函数 0 个

### 函数列表
- `_collect_known_phases(phase_stats)` L14-L19 (~6L)
- `_fit_linear(xs1, xs2, ys)` L22-L75 (~54L)
- `_predict_phase(records, phase_name, project_lines, proposal_chars)` L78-L108 (~31L)
- `_fallback_estimates(phase_stats)` L111-L133 (~23L)
- `predict_change_duration(phase_stats, project_lines, proposal_chars)` L136-L163 (~28L)

### Lint 问题
- 无 lint 问题

### 高复杂度函数 (CC > 10)
- 无高复杂度函数 (CC>10)

## Technical Design
1. 为 `zsiga/duration_predictor.py` 中的公开函数编写单元测试
2. 优先覆盖高复杂度函数: (无高 CC 函数)
3. 使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess）
4. 确保每个测试可独立运行，不依赖运行时环境

### Target Files
- `tests/test_duration_predictor.py` (新建)
- `zsiga/duration_predictor.py` (仅读取分析，不修改)

## Acceptance Criteria
- [BAC-01] 文件 `tests/test_duration_predictor.py` 存在
- [BAC-02] `tests/test_duration_predictor.py` 中存在 `test__collect_known_phases`, `test__fit_linear`, `test__predict_phase`
- [BAC-03] `tests/test_duration_predictor.py` 中存在至少 3 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_duration_predictor.py` 退出码 0

## Scope
- In scope: 为 `zsiga/duration_predictor.py` 编写测试，覆盖公开函数
- Out of scope: 不修改 `zsiga/duration_predictor.py` 源码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（含静态分析数据）
- project=zsiga
