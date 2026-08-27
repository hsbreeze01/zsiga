# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数）补充单元测试。提案声称"缺少测试文件"，但实际上 `tests/test_phase_duration.py`（241 行，9 个测试用例）已覆盖其中 2 个函数（`_fit_linear` 和 `predict_change_duration`）。真正缺少直接测试的是剩余 3 个内部函数：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`。本变更将在**已有测试文件** `tests/test_phase_duration.py` 中追加测试类，或新建 `tests/test_duration_predictor.py` 覆盖缺口函数。

### 拆解后的子任务
- [ ] 1. 在 `tests/test_duration_predictor.py` 中为 `_collect_known_phases` 编写单元测试：空列表、单阶段、多阶段、重复阶段名场景（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 2. 为 `_predict_phase` 编写单元测试：数据充足走线性回归路径、数据不足回退路径、边界值（零/负数输入）（预估复杂度：中, 预估 token：~2500 / 无历史参考）
- [ ] 3. 为 `_fallback_estimates` 编写单元测试：空列表、单条记录、多条记录中位数计算、与已有 `test_phase_duration.py` 不重复的边界场景（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 4. 全部测试通过验证：确保 `python -m pytest tests/test_duration_predictor.py` 退出码 0，且 ruff lint 无错误（预估复杂度：低, 预估 token：~500 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，覆盖 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个缺少直接测试的内部函数
- 测试需可独立运行，不依赖运行时环境（无 LLM 调用、无文件 I/O、无 subprocess）
- 满足 BAC-01 ~ BAC-04 全部验收条件

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有 `tests/test_phase_duration.py`（避免引入回归）
- 不为 `_fit_linear` 和 `predict_change_duration` 重复编写测试（已有覆盖）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块可正常导入（纯 Python，无外部依赖）
- 现有 `tests/test_phase_duration.py` 测试不受影响（新文件独立运行）

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 文件中包含 `test__collect_known_phases`、`test__fit_linear`（可选，已有覆盖）、`test__predict_phase` 三个命名测试函数
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. `python -m pytest tests/test_phase_duration.py` 退出码仍为 0（无回归）
5. `ruff check tests/test_duration_predictor.py` 无错误

### 验收方式
- 文件存在性检查：`test -f tests/test_duration_predictor.py`
- 符号检查：`grep -c 'def test_' tests/test_duration_predictor.py` ≥ 3
- Pytest 通过：`python -m pytest tests/test_duration_predictor.py` 退出码 0
- 无回归：`python -m pytest tests/test_phase_duration.py` 退出码 0
- Lint 通过：`ruff check tests/test_duration_predictor.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（仅读取分析）
- `tests/test_phase_duration.py`（已有 9 个测试，避免回归）
- `zsiga/` 下所有其他源码文件

### 项目部署分支
deploy

### 已知风险
- **测试重复风险**：`test_phase_duration.py` 已覆盖 `_fit_linear`（2 个测试）和 `predict_change_duration`（6 个测试）。新文件应避免重复覆盖这两个函数，专注 3 个缺口函数
- **僵尸提案循环**：此提案已迭代 15+ 轮全部 skipped/archived。本轮若再次 skip，引擎可能继续生成。执行时需确保 BAC 全部通过以打破循环
- **内部函数测试**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 均以下划线开头，属于模块私有函数，需通过 `from zsiga.duration_predictor import _xxx` 直接导入测试

### 预估 token 消耗
- prompt: ~4000
- completion: ~3000
- 数据来源: 无历史参考（此提案历史全部 skipped，无可参考的实际执行记录）
