# clarify.md — add-tests-duration_predictor

> ⚠️ **关键事实**：`tests/test_phase_duration.py`（241 行，9 个测试）已覆盖 `_fit_linear`（2 个）和 `predict_change_duration`（6 个）。本 proposal 的增量价值在于为 **3 个仅间接覆盖的私有函数**（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）补充直接测试，并补齐 `_fit_linear` 的退化边界（共线输入、全零 y、单点退化）。**不得重复** `test_phase_duration.py` 已有场景。

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 函数）创建专用测试文件 `tests/test_duration_predictor.py`，增量覆盖 3 个仅间接测试的私有函数，并补充 `_fit_linear` 的退化边界用例。

### 拆解后的子任务

- [ ] 1. **`_collect_known_phases` 直接测试**：验证从 phase_stats 提取唯一 phase 名的逻辑，包括空输入、单条记录、多条记录含重复 phase、含 `_total` 键等边界（预估复杂度：低，预估 token：~2000 / 无历史参考）
- [ ] 2. **`_predict_phase` 直接测试**：验证单 phase 时长预测，包括 <3 条走 median 回退、≥3 条走线性回归、records 为空、project_lines/proposal_chars 缺失等边界（预估复杂度：中，预估 token：~3000 / 无历史参考）
- [ ] 3. **`_fallback_estimates` 直接测试**：验证 median 回退估算逻辑，包括空输入、单条记录、含 `_total` 键特殊处理、负值钳位等边界（预估复杂度：低，预估 token：~2000 / 无历史参考）
- [ ] 4. **`_fit_linear` 退化边界补充**：共线输入（行列式为零）、全零 ys、单数据点退化等 `test_phase_duration.py` 未覆盖的边界（预估复杂度：中，预估 token：~2500 / 无历史参考）
- [ ] 5. **测试文件骨架与 pytest 验证**：创建 `tests/test_duration_predictor.py`，组织上述测试为合理的测试类，确保 `python -m pytest tests/test_duration_predictor.py` 退出码 0（预估复杂度：低，预估 token：~1500 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 为 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 编写直接单元测试
- 为 `_fit_linear` 补充退化边界测试（不与 `test_phase_duration.py` 重复）
- 通过 `python -m pytest tests/test_duration_predictor.py` 验证全部通过

### OUT of scope
- **不修改** `zsiga/duration_predictor.py` 源码
- **不重复** `tests/test_phase_duration.py` 已有场景（`TestFitLinear.test_known_coefficients`、`test_empty_input`、`TestPredictChangeDurationSufficient`、`TestPredictChangeDurationInsufficient`、`TestNegativeClamping`、`TestMissingPhaseKeys`）
- 不修改 `tests/test_phase_duration.py`

### 依赖的外部条件
- `zsiga/duration_predictor.py` 模块必须可导入（纯标准库依赖 `statistics.median`，无外部依赖）
- `tests/test_phase_duration.py` 已有 9 个测试保持通过（回归保护）
- pytest 可正常运行

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 文件包含 `test__collect_known_phases`、`test__fit_linear`（退化边界）、`test__predict_phase` 三个测试函数名
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. 已有测试 `python -m pytest tests/test_phase_duration.py` 仍全部通过（回归验证）
5. 新测试不与 `test_phase_duration.py` 场景重复

### 验收方式
- `test -f tests/test_duration_predictor.py` 验证文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 计数 ≥ 3
- `python -m pytest tests/test_duration_predictor.py -v` 全部 PASSED
- `python -m pytest tests/test_phase_duration.py -v` 无回归

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（只读分析，不修改源码）
- `tests/test_phase_duration.py`（不修改已有测试）

### 项目部署分支
- deploy

### 已知风险
- **历史循环风险**：此 proposal 已被生成 20+ 次、全部 skip/reject。根因是 proposal 引擎声称"模块缺少测试"但忽视了 `test_phase_duration.py`。本轮 clarify 已明确增量价值，但执行时仍需严格遵守"不重复"约束
- **测试文件命名混淆**：现有测试文件名 `test_phase_duration.py` 不匹配模块名 `duration_predictor`，这是历史遗留问题，本 proposal 不负责解决
- **私有函数测试稳定性**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 是私有函数，未来重构可能改变签名，测试需接受这一风险

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类型测试任务估计）
