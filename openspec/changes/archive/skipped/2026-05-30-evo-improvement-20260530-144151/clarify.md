# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行, 5 函数）补充单元测试覆盖。Proposal 声称模块"缺少测试文件"，但实际上 `tests/test_phase_duration.py`（241 行, 8 个测试）已覆盖其中 2 个函数（`_fit_linear`、`predict_change_duration`）。真正缺少的是剩余 3 个内部函数的直接测试：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`。

### 拆解后的子任务

- [ ] 1. **创建 `tests/test_duration_predictor.py` 并实现 `_collect_known_phases` 测试组** — 覆盖：空输入、单记录、多记录合并去重、缺失 phase_name key、混合数据（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **实现 `_fallback_estimates` 测试组** — 覆盖：空输入返回全零 total、单阶段中位数、多阶段各自独立中位数、total 求和校验、奇数个记录中位数取中间值（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 3. **实现 `_predict_phase` 测试组** — 覆盖：无匹配 phase 走默认值、2 条记录走 median 回退、3+ 条记录走线性回归、负值钳位为 0、单条记录返回值本身（预估复杂度：中, 预估 token：~2500 / 无历史参考）
- [ ] 4. **补充 `_fit_linear` 退化边界测试**（增量，不与 `tests/test_phase_duration.py` 重复）— 覆盖：共线退化走 mean 回退、单点退化、全零 y 值。需确认与现有 `TestFitLinear` 不重复后决定是否添加（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 5. **全量 pytest 验证** — `python -m pytest tests/test_duration_predictor.py` 退出码 0；同时确认 `tests/test_phase_duration.py` 未受影响（预估复杂度：低, 预估 token：~500 / 无历史参考）

## 边界

### IN scope
- 创建 `tests/test_duration_predictor.py`（新文件）
- 为 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase` 编写直接单元测试
- 增量补充 `_fit_linear` 的退化边界用例（不与已有测试重复）
- 满足 BAC-01 ~ BAC-04 验收标准

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有的 `tests/test_phase_duration.py`
- 不修改任何配置文件或项目基础设施
- 不添加 `predict_change_duration` 的测试（已在 `test_phase_duration.py` 充分覆盖）

### 依赖的外部条件
- `zsiga/duration_predictor.py` 中 5 个函数的签名和行为保持稳定
- `tests/test_phase_duration.py` 不被外部修改
- 项目 Python 环境（≥3.10）和 pytest 可用
- 无外部依赖需 mock（模块仅依赖 `statistics.median`，纯计算）

## 目标

### 成功标准
1. 文件 `tests/test_duration_predictor.py` 存在且包含至少 3 个 `def test_` 函数
2. 包含 `test__collect_known_phases`、`test__fit_linear`（增量）、`test__predict_phase` 三个指定测试函数
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. `python -m pytest tests/test_phase_duration.py` 退出码 0（无回归）
5. 3 个此前无直接覆盖的内部函数（`_collect_known_phases`、`_fallback_estimates`、`_predict_phase`）均有 ≥2 个独立测试用例

### 验收方式
- `grep -c "def test_" tests/test_duration_predictor.py` ≥ 3
- `grep -q "test__collect_known_phases" tests/test_duration_predictor.py` && `grep -q "test__predict_phase" tests/test_duration_predictor.py` && `grep -q "test__fit_linear" tests/test_duration_predictor.py`
- `python -m pytest tests/test_duration_predictor.py -v` 全绿
- `python -m pytest tests/test_phase_duration.py -v` 全绿（回归检查）

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`
- `tests/test_phase_duration.py`
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- `deploy`

### 已知风险
- **僵尸循环风险**：此 proposal 已被自演进引擎生成 13+ 次，均因"声称模块无测试但实际已有覆盖"被 skip/reject。本次需确保产出有增量价值，不与 `test_phase_duration.py` 重复
- **与已有测试重复**：`test_phase_duration.py` 的 `TestFitLinear` 已覆盖 `_fit_linear` 的常规路径和空输入，新文件只应补充退化/边界用例
- **内部函数稳定性**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 为私有函数（下划线前缀），未来可能重构；测试应关注行为契约而非实现细节

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 均未成功执行到完成）
