# clarify.md — add-tests-duration_predictor

> **前提修正**：proposal 声称"模块缺少测试文件"，但 `tests/test_phase_duration.py`（241 行，8 个测试）已直接 import 并测试了 `_fit_linear` 和 `predict_change_duration`。本需求拆解基于**真实的覆盖缺口**，而非虚假的"零测试"前提。

---

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py` 中尚未被直接测试的 3 个私有函数（`_collect_known_phases`、`_fallback_estimates`、`_predict_phase`）补充独立单元测试。这些函数目前仅通过公开入口 `predict_change_duration` 间接覆盖，缺少边界条件和退化路径的直接验证。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_duration_predictor.py` 文件骨架，导入 5 个目标函数（`_collect_known_phases`, `_fit_linear`, `_predict_phase`, `_fallback_estimates`, `predict_change_duration`）及 `DEFAULT_PHASE_SECONDS` 常量 (预估复杂度：低, 预估 token：~500 / 无历史参考)
- [ ] 2. 为 `_collect_known_phases` 编写直接测试：空输入→空集、单条记录、多条记录去重合并、缺 `phases` key 的记录 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 3. 为 `_fallback_estimates` 编写直接测试：空输入→`{_total: 0}`、单条记录、多条记录中位数计算、`_total` 等于各 phase 之和 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 4. 为 `_predict_phase` 编写直接测试：无匹配 phase→默认值、<3 条记录→中位数回退、≥3 条→线性回归路径、负值钳位到 0、单条记录退化 (预估复杂度：中, 预估 token：~2000 / 无历史参考)
- [ ] 5. 补充 `_fit_linear` 的退化路径测试（与 `test_phase_duration.py` 中已有测试互补，不重复）：共线退化→均值回退、全零 y→零系数 (预估复杂度：低, 预估 token：~1000 / 无历史参考)
- [ ] 6. 运行 `python -m pytest tests/test_duration_predictor.py` 确认全部通过，运行 `python -m pytest tests/` 确认不破坏已有测试 (预估复杂度：低, 预估 token：~500 / 无历史参考)

---

## 边界

### IN scope
- 创建 `tests/test_duration_predictor.py`，包含 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase` 的直接单元测试
- 补充 `_fit_linear` 退化路径测试（不与 `test_phase_duration.py` 重复）
- 确保 pytest 退出码 0（新文件独立运行 + 全量不回归）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改 `tests/test_phase_duration.py` 已有测试
- 不重构或重命名任何已有文件
- 不为 `predict_change_duration` 重复编写测试（已在 `test_phase_duration.py` 中覆盖）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块不变（当前 164 行，5 个函数）
- `tests/test_phase_duration.py` 已有测试全部通过
- pytest + ruff 可用

---

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 存在且包含至少 3 个 `def test_` 函数
2. `test__collect_known_phases`、`test__fit_linear`（退化路径）、`test__predict_phase` 三个函数名存在于新文件中
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. `python -m pytest tests/` 全量通过（无回归）
5. 新测试不与 `tests/test_phase_duration.py` 中已有测试重复（互补关系）

### 验收方式
- `python -m pytest tests/test_duration_predictor.py -v` 查看测试输出
- `python -m pytest tests/ --tb=short` 确认无回归
- `grep -c 'def test_' tests/test_duration_predictor.py` 计数 ≥ 3
- 对比 `tests/test_phase_duration.py` 确认无重复测试场景

---

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`
- `tests/test_phase_duration.py`
- `tests/conftest_zsiga.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
zsiga-l5-autonomous-engineer

### 已知风险
- **僵尸循环风险**：此 proposal 已被生成 20+ 次、全部 skip/reject。必须明确这是**补充测试**而非"从零创建"，避免与已有 `test_phase_duration.py` 功能重叠
- **命名冲突**：`tests/test_duration_predictor.py` 与 `tests/test_phase_duration.py` 主题高度重叠，需确保互补而非重复
- **导入私有函数**：所有被测函数均为模块级私有（`_` 前缀），需确认 `from zsiga.duration_predictor import _xxx` 路径在当前 Python 环境下可用（已有先例：`test_phase_duration.py` 已成功导入 `_fit_linear`）

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 从未成功执行到 completion）
