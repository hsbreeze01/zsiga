# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数）添加单元测试文件 `tests/test_duration_predictor.py`，覆盖全部 5 个函数。

**关键背景**：已有 `tests/test_phase_duration.py`（241 行，9 个测试）覆盖了 `_fit_linear` 和 `predict_change_duration` 两个函数。本 proposal 的实际增量价值在于为 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个缺少直接测试的私有函数补充覆盖。`_fit_linear` 和 `predict_change_duration` 的测试会与已有文件功能重叠，但 BAC 明确要求新文件中存在 `test__fit_linear`，需遵照执行。

### 拆解后的子任务

- [ ] 1. 创建 `tests/test_duration_predictor.py`，编写 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase` 三个未覆盖函数的直接单元测试 (预估复杂度：中, 预估 token：~3000 / 无历史参考)
- [ ] 2. 在同一文件中补充 `_fit_linear` 和 `predict_change_duration` 的测试以满足 BAC-02 要求，确保与 `test_phase_duration.py` 不矛盾 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 3. 全量 pytest 验证：新文件独立通过 + 整体套件无回归 (预估复杂度：低, 预估 token：~500 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，覆盖 5 个函数
- `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个测试函数名必须存在（BAC-02）
- 至少 3 个 `def test_` 函数（BAC-03）
- `pytest tests/test_duration_predictor.py` 退出码 0（BAC-04）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改已有的 `tests/test_phase_duration.py`
- 不修改任何其他源码或配置文件

### 依赖的外部条件
- `zsiga/duration_predictor.py` 中的 5 个函数签名和导入路径保持不变
- `pytest` 可正常运行
- `ruff` lint 通过

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 测试函数 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 均存在于新文件中
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0
4. `python -m pytest tests/test_phase_duration.py` 仍通过（无回归）
5. `ruff check tests/test_duration_predictor.py` 无错误

### 验收方式
- `test -f tests/test_duration_predictor.py` 确认文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 计数 ≥ 3
- `grep` 确认三个指定测试函数名存在
- `python -m pytest tests/test_duration_predictor.py -v` 退出码 0
- `python -m pytest tests/test_phase_duration.py -v` 退出码 0（回归检查）
- `ruff check tests/test_duration_predictor.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`（只读分析，不修改）
- `tests/test_phase_duration.py`（已有测试，不修改）
- `pyproject.toml`、`requirements.txt`（不新增依赖）

### 项目部署分支
deploy

### 已知风险
- **重叠风险**：新文件中 `_fit_linear` 和 `predict_change_duration` 的测试会与 `test_phase_duration.py` 功能重叠，增加维护成本。缓解：新测试侧重不同边界条件（如退化输入、极端值），与已有测试互补
- **僵尸提案循环**：同名 proposal 已迭代 10+ 轮全部 archived/skipped，原因是 Steward 以"已有测试"为由拒绝。本轮需确保新文件真正提供增量价值（覆盖 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase` 三个未覆盖函数）
- **私有函数测试**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 为模块私有函数，需通过 `from zsiga.duration_predictor import _collect_known_phases` 等方式导入测试

### 预估 token 消耗
- prompt: ~2500
- completion: ~3000
- 数据来源: 无历史参考（同名 proposal 历史均未执行到 implement 阶段）
