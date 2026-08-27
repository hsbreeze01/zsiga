# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为模块 `zsiga/duration_predictor.py`（164 行，5 个函数）添加单元测试文件 `tests/test_duration_predictor.py`，覆盖 `_collect_known_phases`、`_fit_linear`、`_predict_phase`、`_fallback_estimates`、`predict_change_duration` 的核心行为。

### 拆解后的子任务

- [ ] 1. **测试基础设施搭建**：创建 `tests/test_duration_predictor.py`，编写导入、共享 fixture（构造 `phase_stats` 样本数据、`records` 样本数据），确保文件可被 pytest 发现并收集。（预估复杂度：低, 预估 token：~800 / 无历史参考）
- [ ] 2. **内部函数测试组**：为 `_collect_known_phases`（过滤/空输入/单条记录）、`_fit_linear`（充分数据拟合、不足数据回退、边界值）、`_fallback_estimates`（正常回退、空输入、负值钳制）编写测试用例。（预估复杂度：中, 预估 token：~2500 / 无历史参考）
- [ ] 3. **预测链路测试组**：为 `_predict_phase`（有效预测、数据不足回退、缺失阶段键）和 `predict_change_duration`（集成路径：有足够历史 → 返回预测、无历史 → 回退）编写测试用例。（预估复杂度：中, 预估 token：~2000 / 无历史参考）
- [ ] 4. **验收验证**：运行 `python -m pytest tests/test_duration_predictor.py` 确认退出码 0，运行 `ruff check tests/test_duration_predictor.py` 确认无 lint 错误。（预估复杂度：低, 预估 token：~300 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`
- 覆盖 5 个函数的纯逻辑路径（无需 LLM、文件 I/O、subprocess mock——该模块无外部依赖）
- 确保所有测试可独立运行，不依赖运行时环境或数据库

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不修改现有测试文件（如 `tests/test_phase_duration.py`）
- 不涉及覆盖率百分比指标
- 不涉及 dashboard、daemon、config 等其他模块

### 依赖的外部条件
- `zsiga/duration_predictor.py` 中的 5 个函数可被正常 import
- pytest 已安装且 `tests/conftest_zsiga.py` 不干扰新文件

## 目标

### 成功标准
1. 文件 `tests/test_duration_predictor.py` 存在且可被 pytest 收集
2. 包含 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 三个具名测试函数
3. 至少 3 个 `def test_` 函数
4. `python -m pytest tests/test_duration_predictor.py` 退出码 0
5. `ruff check tests/test_duration_predictor.py` 无报错

### 验收方式
- `test -f tests/test_duration_predictor.py` 验证文件存在
- `grep -c 'def test_' tests/test_duration_predictor.py` 验证测试函数数量 ≥ 3
- `grep -E 'def test_(_collect_known_phases|_fit_linear|_predict_phase)' tests/test_duration_predictor.py` 验证具名函数
- `python -m pytest tests/test_duration_predictor.py -x --tb=short` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`
- `tests/test_phase_duration.py`
- `tests/conftest_zsiga.py`
- `tests/test_spec_evo_improvement_20260528_080627__duration_predictor_test_coverage.py`

### 项目部署分支
- 主开发分支（未在 proposal 中指定，遵循项目默认）

### 已知风险
- **与现有测试重叠**：`tests/test_phase_duration.py`（241 行）已包含 `_fit_linear` 和 `predict_change_duration` 的测试（`TestFitLinear`、`TestPredictChangeDurationSufficient`、`TestPredictChangeDurationInsufficient`、`TestNegativeClamping`、`TestMissingPhaseKeys`）。新建 `test_duration_predictor.py` 可能产生重复测试。实现时应聚焦现有文件未直接覆盖的函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`），避免复制已有断言。
- **同名 spec 测试文件已存在**：`tests/test_spec_evo_improvement_20260528_080627__duration_predictor_test_coverage.py` 可能已包含本次 proposal 的部分或全部测试。实现前应检查该文件内容，避免三文件重复覆盖同一模块。
- **纯函数模块无外部依赖**：`duration_predictor.py` 的 5 个函数均为纯计算函数（无 LLM、文件 I/O、subprocess），proposal 中提到的"mock 隔离外部依赖"不适用，可简化测试编写。

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考
