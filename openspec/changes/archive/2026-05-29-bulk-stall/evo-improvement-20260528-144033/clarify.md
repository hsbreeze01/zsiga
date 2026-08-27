# clarify.md — add-tests-duration_predictor

## 需求拆解

### 原始需求
为 `zsiga/duration_predictor.py`（164 行，5 个函数）添加单元测试。Proposal 要求创建 `tests/test_duration_predictor.py`，覆盖公开函数。

### 关键事实（上下文补充）
- `tests/test_phase_duration.py`（241 行，~14 个 test_ 方法）**已存在**，通过 `TestFitLinear`、`TestPredictChangeDurationSufficient`、`TestPredictChangeDurationInsufficient`、`TestNegativeClamping`、`TestMissingPhaseKeys` 等类间接覆盖了 `_fit_linear` 和 `predict_change_duration` 的主要路径。
- 仅 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数缺乏**直接**独立测试（仅通过 `predict_change_duration` 间接覆盖）。
- Proposal 声称"缺少测试文件"的前提部分失实——测试存在但文件名不同。

### 拆解后的子任务

- [ ] 1. **创建 `tests/test_duration_predictor.py` 并覆盖三个直接测试缺口函数** (预估复杂度：中, 预估 token：~4000 / 无历史参考)
  - 为 `_collect_known_phases(phase_stats)` 编写直接测试：多阶段提取、空输入、单阶段
  - 为 `_predict_phase(records, phase_name, project_lines, proposal_chars)` 编写直接测试：正常回归预测、负值钳制、不足记录回退
  - 为 `_fallback_estimates(phase_stats)` 编写直接测试：多阶段中位数计算、空输入、单阶段
  - 文件范围：`tests/test_duration_predictor.py`（新建）

- [ ] 2. **验证测试通过且无 lint 错误** (预估复杂度：低, 预估 token：~500 / 无历史参考)
  - 运行 `python -m pytest tests/test_duration_predictor.py` 确认退出码 0
  - 运行 `ruff check tests/test_duration_predictor.py` 确认无 lint 问题
  - 确认与已有 `tests/test_phase_duration.py` 不产生 import 或 fixture 冲突
  - 文件范围：`tests/test_duration_predictor.py`

## 边界

### IN scope
- 新建 `tests/test_duration_predictor.py`，包含针对 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的直接单元测试
- 测试使用 `importlib` 或直接 import 访问私有函数（项目已有先例：`test_phase_duration.py` 直接导入 `_fit_linear`）
- 测试数据手工构造（参考 `test_phase_duration.py` 中 `_make_stats()` / `_make_changes()` 模式）

### OUT of scope
- 不修改 `zsiga/duration_predictor.py` 源码
- 不重复覆盖已有 `tests/test_phase_duration.py` 中已测试的场景（`_fit_linear` 的空输入/已知系数、`predict_change_duration` 的充分/不充分数据路径、负值钳制、缺失键）
- 不修改 `tests/test_phase_duration.py`

### 依赖的外部条件
- `zsiga/duration_predictor.py` 存在且可导入（已确认）
- pytest 框架可用（已确认）
- 项目已有 `tests/conftest_zsiga.py` 提供 fixture 支持

## 目标

### 成功标准
1. `tests/test_duration_predictor.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 文件中包含 `test__collect_known_phases`、`test__fit_linear`（或等效覆盖）、`test__predict_phase` 三个测试函数名（BAC-02）
3. `python -m pytest tests/test_duration_predictor.py` 退出码 0（BAC-04）
4. 新测试与已有 `tests/test_phase_duration.py` 不产生冲突：`python -m pytest tests/test_phase_duration.py tests/test_duration_predictor.py` 全部通过
5. 新测试覆盖 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个已有测试中未直接覆盖的函数

### 验收方式
- 自动验证：`python -m pytest tests/test_duration_predictor.py -v` 退出码 0
- 自动验证：`ruff check tests/test_duration_predictor.py` 无错误
- 自动验证：`grep -c "def test_" tests/test_duration_predictor.py` 输出 ≥ 3
- 自动验证：`grep -E "test__collect_known_phases|test__predict_phase" tests/test_duration_predictor.py` 匹配成功
- 回归验证：`python -m pytest tests/test_phase_duration.py` 仍然通过

## 约束

### 不能修改的文件
- `zsiga/duration_predictor.py`
- `tests/test_phase_duration.py`
- `tests/conftest_zsiga.py`

### 项目部署分支
- `premium`

### 已知风险
- **与已有测试重叠**：`tests/test_phase_duration.py` 已覆盖 `_fit_linear` 和 `predict_change_duration`，新文件不应重复相同测试场景
- **私有函数测试稳定性**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 是私有函数，未来可能被重构或重命名
- **Proposal 历史风险**：同类 auto-generated 测试 proposal 在 proposal_gate 多次被 reject/pushback（至少 6 次归档），需确保本次不重复失败模式

### 预估 token 消耗
- prompt: ~3500
- completion: ~2500
- 数据来源: 无历史参考（同类任务无成功执行记录，仅参考 `test_phase_duration.py` 的测试编写模式）
