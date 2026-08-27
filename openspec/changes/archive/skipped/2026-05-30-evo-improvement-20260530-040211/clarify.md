# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个纯函数，零外部依赖）创建独立测试文件 `tests/test_duration_predictor.py`，补充三个尚无直接单元测试的私有函数的覆盖。

> **前提修正**：proposal 原文声称"模块缺少测试文件"，但 `tests/test_phase_duration.py`（241 行，6 类，15 用例）已直接覆盖 `_fit_linear`（2 用例）和 `predict_change_duration`（7 用例）。本 clarify 仅聚焦**增量价值**：为 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 添加直接测试。

### 拆解后的子任务

- [ ] 1. **为 `_collect_known_phases` 编写直接单元测试** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 文件范围：`tests/test_duration_predictor.py`（新建）
  - 测试场景：正常多条记录返回去重 phase 集合；空列表返回空集；单条记录返回其所有 phase 键；重复 phase 仅保留唯一值
  - 数据 schema：`list[dict]`（注意：与 `metrics/collector.py` 的 `dict[str, dict]` 不同）

- [ ] 2. **为 `_predict_phase` 编写直接单元测试** (预估复杂度：中, 预估 token：~2500 / 无历史参考)
  - 文件范围：`tests/test_duration_predictor.py`
  - 测试场景：≥3 条记录走线性回归路径返回预测值；<3 条记录走 median 回退；目标 phase 不存在时降级；不同 project_lines/proposal_chars 组合对预测的影响
  - 需要理解 `_fit_linear` 的返回值结构以构造合理的 `_predict_phase` 输入

- [ ] 3. **为 `_fallback_estimates` 编写直接单元测试** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 文件范围：`tests/test_duration_predictor.py`
  - 测试场景：正常 stats 输入返回包含 `_total` 求和的回退估计；空列表返回合理默认值；单条记录返回基于唯一值的估计

- [ ] 4. **集成验证与回归检查** (预估复杂度：低, 预估 token：~800 / 无历史参考)
  - 文件范围：`tests/test_duration_predictor.py`（最终验证）
  - 验证：`python -m pytest tests/test_duration_predictor.py` 退出码 0；`python -m pytest tests/test_phase_duration.py` 退出码 0（旧测试不回归）；ruff lint 无报错

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含至少 3 个 `def test_` 函数
- 直接测试 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数
- 所有测试纯函数调用，零 mock（模块无外部依赖）
- 通过 `from zsiga.duration_predictor import _collect_known_phases, _predict_phase, _fallback_estimates` 导入

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不重复测试 `_fit_linear`（已有 `TestFitLinear` 覆盖）
- 不重复测试 `predict_change_duration`（已有 6 个测试类覆盖）
- 不修改或合并 `tests/test_phase_duration.py`
- 不添加 conftest fixture 或共享测试基础设施

### 依赖的外部条件
- `zsiga/duration_predictor.py` 源码在实施期间不可变（只读参考）
- `tests/test_phase_duration.py` 必须保持通过（回归保护）
- pytest 和 ruff 可用（项目已配置）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. `test__collect_known_phases`、`test__predict_phase`、`test__fallback_estimates` 三个函数名存在于新文件中
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0（全部通过）
4. `python -m pytest tests/test_phase_duration.py` 退出码 0（旧测试不回归）
5. ruff lint 对新文件零报错

### 验收方式
- `test -f tests/test_duration_predictor.py` 确认文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 确认测试数量
- `python -m pytest tests/test_duration_predictor.py -v` 确认全部通过
- `python -m pytest tests/test_phase_duration.py -v` 确认旧测试不回归
- `ruff check tests/test_duration_predictor.py` 确认无 lint 问题

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析，不修改）
- `tests/test_phase_duration.py`（保持不动）
- `zsiga/` 下所有源码文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
deploy

### 已知风险
- **重复提案循环**：此 proposal 已迭代 22+ 次（全部 archived/skipped），原因是自动生成的 proposal 前提虚假（声称"模块无测试"）。本 clarify 已修正前提，聚焦增量价值，但实施者需注意不要重复测试已覆盖的函数
- **私有函数测试争议**：直接测试 `_` 前缀私有函数是合理的（纯函数、无副作用、无外部依赖），但需通过显式 import 而非 `from module import *`
- **数据 schema 混淆**：`duration_predictor.py` 使用 `list[dict]` schema，而 `metrics/collector.py` 使用 `dict[str, dict]` schema，测试数据构造需严格对齐前者
- **低风险**：仅添加测试文件，无源码变更，最坏情况删除新文件即可回退

### 预估 token 消耗
- prompt: ~6000（源码阅读 + 已有测试分析 + 上下文）
- completion: ~3000（3 组测试函数 + imports + docstrings）
- 数据来源: 无历史参考（同类任务 22+ 次均未到达实施阶段）
